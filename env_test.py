from dotenv import load_dotenv
import os
print("📁 Current working directory:", os.getcwd())
print("📄 Files in this folder:", os.listdir())

# Load environment variables from .env file in same directory
load_dotenv()

api_key = os.getenv("APCA_API_KEY_ID")
secret_key = os.getenv("APCA_API_SECRET_KEY")

print("🔍 Loaded API Key:", repr(api_key))
print("🔍 Loaded Secret:", repr(secret_key))
