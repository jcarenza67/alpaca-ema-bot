# 🦅 Alpaca EMA Trading Bot

An automated swing trading bot using the Alpaca Paper Trading API and a simple EMA crossover strategy. Monitors selected stocks, executes trades based on EMA signals, and sends real-time Discord alerts.

---

## 🚀 Features

- 📈 EMA(9) / EMA(21) crossover buy signals  
- 💰 10% take-profit / -20% stop-loss logic  
- ⏳ Holds positions for at least 1 day (swing trading enforcement)  
- 🧠 Position tracking in JSON  
- 🗃️ Trade logging to CSV  
- 🔔 Discord webhook alerts for buys and sells  
- 🕒 Automatically starts 30 minutes before market open (via cron)  
- 💤 Auto shuts down after market close  
- 🧹 Weekly auto-deletes log files (via cron)  

---

## Create Your .env File

- APCA_API_KEY_ID=your_alpaca_paper_key
- APCA_API_SECRET_KEY=your_alpaca_secret
- DISCORD_WEBHOOK_URL=<https://discord.com/api/webhooks/your_webhook_url>

## Install Dependencies

- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

## Manual Test

`
python3 ema_test.py
`

### You should see

- 🚀 Starting EMA bot. Market-aware loop is running...
- 🏁 Market closed — exiting bot.

## 🛣️ Roadmap (Ideas)

- 💬 Sentiment-based SPY options module

- 📊 Backtesting support

- 🧠 Strategy toggles (RSI, SMA, MACD)

- 📱 Telegram or SMS alert integration

## 🛡️ License

- This repo is private/personal. No license yet.
