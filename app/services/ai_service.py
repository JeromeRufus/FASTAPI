from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from app.services.gemini_client import client, GEMINI_MODEL
from app.services.retrieval_service import retrieve_exact_context, retrieve_context_from_intent
from app.services.intent_service import extract_intent
from app.exceptions.custom_exception import AIServiceUnavailableException


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

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=question
        )
    except genai_errors.APIError:
        raise AIServiceUnavailableException()

    return response.text


# =========================================================
# RETRIEVAL-AUGMENTED GENERATION
# =========================================================
# Two-stage retrieval:
#   1. Fast path - regex-matched exact IDs/emails, no LLM call.
#   2. Fallback - Gemini classifies the question into a
#      structured query plan (entity/operation/filters), which
#      is then executed as a normal SQLAlchemy query. This is
#      what handles arbitrary phrasing ("how many", "highest
#      balance", "savings and loan accounts", "what types
#      exist", etc.) without hand-written regex per pattern.

def ask_gemini_with_context(db: Session, question: str):

    context_lines, sources = retrieve_exact_context(db, question)

    if not context_lines:
        intent = extract_intent(db, question)
        if intent and intent.get("entity"):
            context_lines, sources = retrieve_context_from_intent(db, intent)

    if context_lines:
        context_text = "\n".join(f"- {line}" for line in context_lines)
    else:
        context_text = "(No matching customer, account, or transaction records were found.)"

    prompt = RAG_PROMPT_TEMPLATE.format(
        context=context_text,
        question=question
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
    except genai_errors.APIError:
        raise AIServiceUnavailableException()

    return response.text, sources