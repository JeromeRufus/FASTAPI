import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from app.services.retrieval_service import retrieve_context


# Load environment variables
load_dotenv()


# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not configured"
    )


# Create Gemini client
client = genai.Client(
    api_key=api_key
)


# =========================================================
# PROMPT TEMPLATE
# =========================================================

RAG_PROMPT_TEMPLATE = """You are a customer account assistant. \
Answer the question using ONLY the account data below. \
Do not use any outside knowledge, and do not invent account numbers, \
balances, or customer details that are not present in the data. \
If the data below doesn't contain what's needed to answer, say so \
clearly instead of guessing.

Account data:
{context}

Question: {question}"""


# =========================================================
# PLAIN GEMINI CALL (no retrieval) - kept for reference
# =========================================================

def ask_gemini(question: str) -> str:

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=question
    )

    return response.text


# =========================================================
# RETRIEVAL-AUGMENTED GENERATION
# =========================================================

def ask_gemini_with_context(db: Session, question: str):

    context_lines, sources = retrieve_context(db, question)

    if context_lines:
        context_text = "\n".join(f"- {line}" for line in context_lines)
    else:
        context_text = "(No matching customer, account, or transaction records were found.)"

    prompt = RAG_PROMPT_TEMPLATE.format(
        context=context_text,
        question=question
    )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    return response.text, sources
