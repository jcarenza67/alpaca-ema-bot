import requests
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(message):
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code == 204:
            print("✅ Message sent successfully.")
        else:
            print(f"⚠️ Failed to send message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

send_discord_alert("This is a test to make sure the bot is sending messages from my script to discord.")
