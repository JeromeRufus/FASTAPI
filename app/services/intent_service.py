import json

from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from app.services.gemini_client import client, GEMINI_MODEL
from app.services.query_helpers import distinct_values
from app.models.account import Account
from app.models.transaction import Transaction
from app.exceptions.custom_exception import AIServiceUnavailableException


# =========================================================
# INTENT CLASSIFICATION PROMPT
# =========================================================
# Rather than hand-writing regex for every possible phrasing
# ("how many", "highest balance", "savings and loan accounts",
# "what types exist", etc.), we ask Gemini to read the question
# once and translate it into a structured query plan. The real
# distinct values from the DB are included so the model maps
# synonyms ("loan account") onto the exact stored strings
# ("LOAN") instead of us guessing.

INTENT_PROMPT_TEMPLATE = """You convert a natural-language question about a bank's \
customer/account/transaction database into a structured JSON query plan.

Known values currently stored in the database (map anything the question refers to, \
including synonyms or loose phrasing, onto these EXACT strings):
- account_type values: {account_types}
- account status values: {statuses}
- transaction_type values: {transaction_types}

Return ONLY valid JSON, no markdown formatting, no explanation, matching exactly this shape:
{{
  "entity": "customer" | "account" | "transaction" | null,
  "operation": "lookup" | "count" | "sum" | "max" | "min" | "list" | "distinct" | null,
  "customer_number": string or null,
  "account_number": string or null,
  "transaction_number": string or null,
  "email": string or null,
  "name_contains": string or null,
  "account_types": [string, ...],
  "statuses": [string, ...],
  "transaction_types": [string, ...],
  "balance_gt": number or null,
  "balance_lt": number or null,
  "amount_gt": number or null,
  "amount_lt": number or null,
  "distinct_field": "account_type" | "status" | "transaction_type" | null,
  "limit": integer or null
}}

Rules:
- "entity" is the primary table the question is about.
- Use "lookup" when a specific customer/account/transaction number or email is given.
- Use "count" for "how many" / bare mentions of "records" with no other qualifier.
- Use "sum" for "total"/"sum of" style questions.
- Use "max"/"min" for "highest"/"lowest"/"top" style questions. If a specific number of \
results is requested (e.g. "top 5"), set "limit" to that number, otherwise leave "limit" null.
- Use "distinct" for "what types/statuses/kinds exist" style questions, and set "distinct_field".
- Use "list" for anything else asking to see multiple matching records (including filtered \
sets like "accounts under savings and loan" - include BOTH values in "account_types").
- Map every account type / status / transaction type mentioned (however loosely phrased) to \
the closest matching value(s) from the known values above. Include multiple values in the \
list if more than one is mentioned.
- Leave irrelevant fields null, or an empty list for the list-type fields.
- If the question has nothing to do with this database, set "entity" to null.

Question: {question}"""


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            if first_line.strip().lower() in ("json", ""):
                text = rest
    return text.strip()


def extract_intent(db: Session, question: str) -> dict | None:
    """
    Asks Gemini to classify the question into a structured query plan.
    Returns None if the response can't be parsed as valid JSON -
    callers should treat that the same as "no intent detected".
    """

    prompt = INTENT_PROMPT_TEMPLATE.format(
        account_types=", ".join(distinct_values(db, Account.account_type)) or "(none stored yet)",
        statuses=", ".join(distinct_values(db, Account.status)) or "(none stored yet)",
        transaction_types=", ".join(distinct_values(db, Transaction.transaction_type)) or "(none stored yet)",
        question=question,
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
    except genai_errors.APIError:
        raise AIServiceUnavailableException()

    try:
        return json.loads(_strip_code_fence(response.text))
    except (json.JSONDecodeError, ValueError, AttributeError):
        return None