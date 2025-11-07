import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
REDIS_URL = os.getenv("REDIS_URL")
# URL for the collector service (e.g. http://collector-service:8080)
COLLECTOR_SERVICE_URL = os.getenv("COLLECTOR_SERVICE_URL", "http://127.0.0.1:8080")

# Secret shared with ML service for price callbacks. Set in env as ML_CALLBACK_SECRET.
ML_CALLBACK_SECRET = os.getenv("ML_CALLBACK_SECRET")