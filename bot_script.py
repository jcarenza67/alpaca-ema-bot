import requests
import os
from dotenv import load_dotenv

# Force explicit path to the .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(dotenv_path=env_path)

# Get keys
api_key = os.getenv("APCA_API_KEY_ID")
secret_key = os.getenv("APCA_API_SECRET_KEY")

# Debug print
print("Current working directory:", script_dir)
print(".env file contents:")
with open(env_path, "r") as f:
    print(f.read())

print("Loaded API Key:", repr(api_key))
print("Loaded Secret:", repr(secret_key))

# Alpaca paper trading API base URL
BASE_URL = "https://paper-api.alpaca.markets/v2"

# Headers for authentication
HEADERS = {
    "APCA-API-KEY-ID": api_key,
    "APCA-API-SECRET-KEY": secret_key,
}

# Define a basic market buy order for 1 share of AAPL
order = {
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy",
    "type": "market",
    "time_in_force": "gtc"
}

# Submit the order
response = requests.post(f"{BASE_URL}/orders", json=order, headers=HEADERS)

# Check and print the result
if response.status_code in [200, 201]:
    print("Trade placed successfully!")
    print(response.json())
else:
    print("Error placing trade:", response.status_code, response.text)
