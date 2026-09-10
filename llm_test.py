import os

from dotenv import load_dotenv
from google import genai


# Load .env file
load_dotenv()

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not loaded. Check your .env file."
    )

# Create Gemini client
client = genai.Client(api_key=api_key)


# Send request to Gemini
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain what a bank account is in simple terms."
)


# Print response
print(response.text)