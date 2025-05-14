import os
import time
import json
import csv
import pandas as pd
import pytz
import requests
from datetime import datetime, timedelta
from alpaca_trade_api.rest import REST, TimeFrame
from ta.momentum import RSIIndicator
from dotenv import load_dotenv

from datetime import datetime
with open("/Users/josephwilfong/alpaca-bot/ema_bot_log.txt", "a") as f:
    f.write(f"[{datetime.now().isoformat()}] 📡 Cron triggered bot\n")



# ==== CONFIG ====
POSITION_FILE = "positions.json"
TRADE_LOG_FILE = "trade_log.csv"
symbols = {
    "AAPL": 1,
    "NVDA": 1,
    "TSLA": 1,
    "NMAX": 1,
    "PLTR": 1,
    "PYPL": 1,
    "GOOGL": 1,
    "MSTR": 1,
    "SPY": 1,
    "AUR": 200,
    "RGTI": 200,
    "MARA": 200,
    "SAVA": 200,
    "KULR": 200,
    "NIO": 200,
}

eastern = pytz.timezone("US/Eastern")

# ==== ENV SETUP ====
load_dotenv()
API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"
api = REST(API_KEY, SECRET_KEY, BASE_URL)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(message):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {e}")

# ==== HELPERS ====
def is_market_open():
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    today = now.date()
    market_open = eastern.localize(datetime.combine(today, datetime.strptime("09:30", "%H:%M").time()))
    market_close = eastern.localize(datetime.combine(today, datetime.strptime("16:00", "%H:%M").time()))
    return market_open <= now <= market_close

def already_in_position(symbol):
    if not os.path.exists(POSITION_FILE):
        return False
    with open(POSITION_FILE, "r") as f:
        positions = json.load(f)
    return symbol in positions

def load_positions():
    if os.path.exists(POSITION_FILE):
        with open(POSITION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_positions(data):
    with open(POSITION_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_trade(symbol, entry_price, exit_price, entry_date, exit_date, reason):
    gain_pct = (exit_price - entry_price) / entry_price * 100
    file_exists = os.path.isfile(TRADE_LOG_FILE)
    with open(TRADE_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["symbol", "entry_price", "exit_price", "gain_pct", "entry_date", "exit_date", "reason"])
        writer.writerow([
            symbol,
            round(entry_price, 2),
            round(exit_price, 2),
            round(gain_pct, 2),
            entry_date,
            exit_date,
            reason
        ])

# ==== BUY LOGIC ====
def check_buy_signal(symbol, qty):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # more days for EMAs & RSI

        bars = api.get_bars(
            symbol,
            TimeFrame.Day,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            feed='iex'
        ).df

        if bars.empty or len(bars) < 30:
            print(f"⚠️ Not enough data for {symbol}")
            return

        bars = bars.reset_index()
        bars["EMA_9"] = bars["close"].ewm(span=9, adjust=False).mean()
        bars["EMA_15"] = bars["close"].ewm(span=15, adjust=False).mean()
        bars["EMA_65"] = bars["close"].ewm(span=65, adjust=False).mean()
        bars["EMA_200"] = bars["close"].ewm(span=200, adjust=False).mean()

        # RSI(14)
        bars["RSI_14"] = RSIIndicator(close=bars["close"], window=14).rsi()

        # Volume spike detection
        bars["Volume_Avg20"] = bars["volume"].rolling(window=20).mean()

        # Pivot Point calculation: (H + L + C) / 3
        bars["Pivot"] = (bars["high"] + bars["low"] + bars["close"]) / 3

        today = bars.iloc[-1]
        yesterday = bars.iloc[-2]

        rsi_ok = today["RSI_14"] < 30
        volume_ok = today["volume"] > 1.5 * today["Volume_Avg20"]
        ema_cross_ok = (
            yesterday["EMA_9"] < yesterday["EMA_15"] and
            today["EMA_9"] > today["EMA_15"]
        )
        price_above_pivot = today["close"] > today["Pivot"]

        print(f"🔍 {symbol}: RSI={today['RSI_14']:.2f}, Vol Spike={volume_ok}, EMA Cross={ema_cross_ok}, Pivot Break={price_above_pivot}")

        if rsi_ok and volume_ok and ema_cross_ok and price_above_pivot:
            print(f"📈 Buy Signal for {symbol}")

            if already_in_position(symbol):
                print(f"⚠️ Already in position: {symbol}")
                return

            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type="market",
                time_in_force="gtc"
            )
            print(f"✅ Bought 1 share of {symbol} at {today['close']}")

            send_discord_alert(f"📈 BUY: {symbol} @ {today['close']:.2f}")

            positions = load_positions()
            positions[symbol] = {
                "entry_price": today["close"],
                "entry_date": datetime.now().isoformat()
            }
            save_positions(positions)
        else:
            print(f"💤 No Buy Signal for {symbol}")

    except Exception as e:
        print(f"❌ Error checking {symbol}: {e}")

# ==== MONITOR + SELL LOGIC ====
def monitor_positions():
    positions = load_positions()
    updated_positions = {}

    try:
        live_positions = {p.symbol: float(p.avg_entry_price) for p in api.list_positions()}
        for symbol, entry_price in live_positions.items():
            if symbol not in positions:
                print(f"🧩 Syncing live Alpaca position: {symbol}")
                positions[symbol] = {
                    "entry_price": entry_price,
                    "entry_date": datetime.now().isoformat()
                }
    except Exception as e:
        print("❌ Failed to sync Alpaca positions:", e)

    for symbol, data in positions.items():
        try:
            entry_price = float(data["entry_price"])
            entry_date = datetime.fromisoformat(data["entry_date"])
            now = datetime.now()

            if now - entry_date < timedelta(days=1):
                print(f"⏳ Holding {symbol}, swing rule active.")
                updated_positions[symbol] = data
                continue

            bars = api.get_bars(symbol, TimeFrame.Minute, limit=1, feed="iex").df
            if bars.empty:
                print(f"⚠️ No recent data for {symbol}")
                updated_positions[symbol] = data
                continue

            current_price = bars["close"].iloc[-1]
            gain_pct = (current_price - entry_price) / entry_price * 100
            print(f"📊 {symbol} @ {current_price:.2f} | Gain: {gain_pct:.2f}%")

            if gain_pct >= 10:
                print(f"🎯 Take-Profit hit → Selling {symbol}")
                api.submit_order(
                    symbol=symbol,
                    qty=1,
                    side="sell",
                    type="market",
                    time_in_force="gtc"
                )
                log_trade(symbol, entry_price, current_price, data["entry_date"], now.isoformat(), "take-profit")
                
                send_discord_alert(
                    f"💰 SELL (TP): {symbol} @ {current_price:.2f} | Gain: {gain_pct:.2f}%"
                )


            elif gain_pct <= -20:
                print(f"💥 Stop-Loss hit → Selling {symbol}")
                api.submit_order(
                    symbol=symbol,
                    qty=1,
                    side="sell",
                    type="market",
                    time_in_force="gtc"
                )
                log_trade(symbol, entry_price, current_price, data["entry_date"], now.isoformat(), "stop-loss")
                
                send_discord_alert(
                    f"🔻 SELL (SL): {symbol} @ {current_price:.2f} | Loss: {gain_pct:.2f}%"
                )


            else:
                updated_positions[symbol] = data
        except Exception as e:
            print(f"❌ Error monitoring {symbol}: {e}")
            updated_positions[symbol] = data

    save_positions(updated_positions)

print("🚀 Starting EMA bot. Market-aware loop is running...\n")
send_discord_alert(f"🟢 EMA bot started at {datetime.now(eastern).strftime('%I:%M %p ET')}")

try:
    while is_market_open():
        print(f"✅ Market is open — checking strategy at {datetime.now(eastern).strftime('%I:%M:%S %p')}...\n")
        for symbol, qty in symbols.items():
            check_buy_signal(symbol, qty)

        monitor_positions()

        print("⏲️ Sleeping for 5 minutes...\n")
        time.sleep(300)

    msg = f"🏁 Market closed — bot exiting at {datetime.now(eastern).strftime('%I:%M %p ET')}"
    print(msg)
    send_discord_alert(msg)


except KeyboardInterrupt:
    print("🛑 Bot manually stopped.")
