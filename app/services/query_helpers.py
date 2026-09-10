import os

from dotenv import load_dotenv
from google import genai


# Load environment variables
load_dotenv()


# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not configured"
    )


# Shared Gemini client - imported by ai_service.py and intent_service.py
client = genai.Client(
    api_key=api_key
)


# Centralized model name so both services stay in sync
GEMINI_MODEL = "gemini-3-flash-preview"