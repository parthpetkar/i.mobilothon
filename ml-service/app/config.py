import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JSON_OUTPUT_DIR = os.getenv("JSON_OUTPUT_DIR", "./data")

# Backend service configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8002")
ML_CALLBACK_SECRET = os.getenv("ML_CALLBACK_SECRET")

# Ensure output directory exists
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
