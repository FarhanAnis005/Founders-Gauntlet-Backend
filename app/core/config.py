# app/core/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file at the project root
load_dotenv()

CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY")
CLERK_WEBHOOK_SECRET = os.environ.get("CLERK_WEBHOOK_SECRET")
CLERK_AUTHORIZED_PARTY = os.getenv("CLERK_AUTHORIZED_PARTY") 
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "./data/uploads")).resolve()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 