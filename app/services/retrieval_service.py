import re

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction


# =========================================================
# ENTITY EXTRACTION (exact ID / email lookups)
# =========================================================
# Your IDs follow predictable prefixes (CUST/ACC/TXN + 8 hex
# chars), so we can pull them straight out of the question
# with a regex instead of needing an embedding model.

CUSTOMER_NUMBER_RE = re.compile(r"\bCUST[0-9A-F]{8}\b", re.IGNORECASE)
ACCOUNT_NUMBER_RE = re.compile(r"\bACC[0-9A-F]{8}\b", re.IGNORECASE)
TRANSACTION_NUMBER_RE = re.compile(r"\bTXN[0-9A-F]{8}\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")


def extract_entities(question: str):

    return {
        "customer_numbers": [m.upper() for m in CUSTOMER_NUMBER_RE.findall(question)],
        "account_numbers": [m.upper() for m in ACCOUNT_NUMBER_RE.findall(question)],
        "transaction_numbers": [m.upper() for m in TRANSACTION_NUMBER_RE.findall(question)],
        "emails": EMAIL_RE.findall(question),
    }


# =========================================================
# RECORD FORMATTERS
# =========================================================

def format_customer(customer: Customer) -> str:
    return (
        f"Customer {customer.customer_number}: "
        f"{customer.first_name} {customer.last_name}, "
        f"email={customer.email}, phone={customer.phone}"
    )


def format_account(account: Account) -> str:
    return (
        f"Account {account.account_number} "
        f"(owner customer {account.customer_number}): "
        f"type={account.account_type}, balance={account.balance}, "
        f"status={account.status}"
    )


def format_transaction(transaction: Transaction) -> str:
    return (
        f"Transaction {transaction.transaction_number} "
        f"on account {transaction.account_number}: "
        f"type={transaction.transaction_type}, amount={transaction.amount}, "
        f"balance_after={transaction.balance_after}, "
        f"created_at={transaction.created_at}"
    )


# =========================================================
# AGGREGATE / LIST INTENT DETECTION
# =========================================================
# Handles questions like "how many accounts are there?",
# "list all active accounts", "total balance of savings
# accounts", "which accounts have balance over 10000".
# This is a *separate* path from the exact-ID lookup above -
# it runs a filtered/aggregated DB query instead of fetching
# one specific row.

COUNT_RE = re.compile(r"\b(how many|count|number of)\b", re.IGNORECASE)
SUM_RE = re.compile(r"\b(total balance|total amount|sum of|total of)\b", re.IGNORECASE)
LIST_RE = re.compile(
    r"\b(list|show all|show me all|all accounts|all customers|"
    r"all transactions|which accounts|which customers)\b",
    re.IGNORECASE,
)
MAX_RE = re.compile(r"\b(highest|maximum|max|largest|greatest|biggest|top)\b", re.IGNORECASE)
MIN_RE = re.compile(r"\b(lowest|minimum|min|smallest)\b", re.IGNORECASE)
TOP_N_RE = re.compile(r"\btop\s+(\d+)\b", re.IGNORECASE)

# "What are the account types?" / "what statuses exist?" -
# asking what distinct values a field can take, not about a
# specific record.
QUESTION_WORD_RE = re.compile(r"\b(what|which|distinct|unique)\b", re.IGNORECASE)
TYPE_OR_STATUS_RE = re.compile(r"\b(types?|kinds?|categories|status(?:es)?)\b", re.IGNORECASE)

# Bare mention of "record(s)" with no explicit list/sum keyword
# is treated as a count fallback - catches loosely-worded phrasing
# like "how records on the account table?" (missing "many").
RECORDS_FALLBACK_RE = re.compile(r"\brecords?\b", re.IGNORECASE)

OVER_RE = re.compile(
    r"(?:over|above|more than|greater than|>)\s*\$?\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)
UNDER_RE = re.compile(
    r"(?:under|below|less than|<)\s*\$?\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _to_number(text: str) -> float:
    return float(text.replace(",", ""))


def _entity_from_question(question: str):
    q = question.lower()
    if "transaction" in q:
        return "transaction"
    if "account" in q:
        return "account"
    if "customer" in q:
        return "customer"
    return None


def _distinct_values(db: Session, column) -> list[str]:
    return [row[0] for row in db.query(column).distinct().all() if row[0]]


def _matched_value(question: str, values: list[str]):
    q = question.lower()
    for value in values:
        if value and value.lower() in q:
            return value
    return None


def detect_aggregate_intent(question: str):
    """
    Returns None if this isn't an aggregate/list-style question.
    Otherwise returns a dict describing what to query.
    """

    entity = _entity_from_question(question)
    if entity is None:
        return None

    # Order matters: superlative phrasing ("highest balance") is
    # checked first since it's the most specific, then explicit
    # "list" phrasing, then sum/count, with a bare-"records"
    # fallback last.
    if MAX_RE.search(question):
        operation = "max"
    elif MIN_RE.search(question):
        operation = "min"
    elif LIST_RE.search(question):
        operation = "list"
    elif SUM_RE.search(question):
        operation = "sum"
    elif COUNT_RE.search(question):
        operation = "count"
    elif QUESTION_WORD_RE.search(question) and TYPE_OR_STATUS_RE.search(question):
        operation = "distinct"
    elif RECORDS_FALLBACK_RE.search(question):
        operation = "count"
    else:
        return None

    top_n_match = TOP_N_RE.search(question)
    limit = int(top_n_match.group(1)) if top_n_match else 1

    over_match = OVER_RE.search(question)
    under_match = UNDER_RE.search(question)

    return {
        "limit": limit,
        "entity": entity,
        "operation": operation,
        "over": _to_number(over_match.group(1)) if over_match else None,
        "under": _to_number(under_match.group(1)) if under_match else None,
    }


def _apply_account_filters(db: Session, query, question: str, intent: dict):
    status = _matched_value(question, _distinct_values(db, Account.status))
    if status:
        query = query.filter(Account.status == status)

    account_type = _matched_value(question, _distinct_values(db, Account.account_type))
    if account_type:
        query = query.filter(Account.account_type == account_type)

    if intent["over"] is not None:
        query = query.filter(Account.balance > intent["over"])
    if intent["under"] is not None:
        query = query.filter(Account.balance < intent["under"])

    return query


def _apply_transaction_filters(db: Session, query, question: str, intent: dict):
    txn_type = _matched_value(question, _distinct_values(db, Transaction.transaction_type))
    if txn_type:
        query = query.filter(Transaction.transaction_type == txn_type)

    if intent["over"] is not None:
        query = query.filter(Transaction.amount > intent["over"])
    if intent["under"] is not None:
        query = query.filter(Transaction.amount < intent["under"])

    return query


def retrieve_aggregate_context(db: Session, question: str, intent: dict, max_records: int = 20):

    context_lines = []
    sources = []

    entity = intent["entity"]
    operation = intent["operation"]

    if entity == "account":
        query = _apply_account_filters(db, db.query(Account), question, intent)

        if operation == "distinct":
            is_status = bool(re.search(r"status", question, re.IGNORECASE))
            column = Account.status if is_status else Account.account_type
            label = "status" if is_status else "type"
            values = _distinct_values(db, column)
            context_lines.append(
                f"Distinct account {label} values in use: "
                f"{', '.join(values) if values else 'none found'}"
            )
            sources.append({"type": "aggregate", "id": f"distinct_account_{label}"})

        elif operation == "count":
            total = query.count()
            context_lines.append(f"Total number of accounts matching the filters: {total}")
            sources.append({"type": "aggregate", "id": "count_accounts"})

        elif operation == "sum":
            total = query.with_entities(func.sum(Account.balance)).scalar() or 0
            context_lines.append(f"Sum of balances for matching accounts: {total}")
            sources.append({"type": "aggregate", "id": "sum_accounts_balance"})

        elif operation in ("max", "min"):
            order = Account.balance.desc() if operation == "max" else Account.balance.asc()
            rows = query.order_by(order).limit(intent["limit"]).all()
            label = "Highest" if operation == "max" else "Lowest"
            context_lines.append(f"{label} balance account(s):")
            for account in rows:
                context_lines.append(format_account(account))
                sources.append({"type": "account", "id": account.account_number})

        elif operation == "list":
            total = query.count()
            rows = query.order_by(Account.id).limit(max_records).all()
            context_lines.append(
                f"Found {total} matching accounts (showing {len(rows)})."
            )
            for account in rows:
                context_lines.append(format_account(account))
                sources.append({"type": "account", "id": account.account_number})

    elif entity == "transaction":
        query = _apply_transaction_filters(db, db.query(Transaction), question, intent)

        if operation == "distinct":
            values = _distinct_values(db, Transaction.transaction_type)
            context_lines.append(
                f"Distinct transaction type values in use: "
                f"{', '.join(values) if values else 'none found'}"
            )
            sources.append({"type": "aggregate", "id": "distinct_transaction_type"})

        elif operation == "count":
            total = query.count()
            context_lines.append(f"Total number of transactions matching the filters: {total}")
            sources.append({"type": "aggregate", "id": "count_transactions"})

        elif operation == "sum":
            total = query.with_entities(func.sum(Transaction.amount)).scalar() or 0
            context_lines.append(f"Sum of amounts for matching transactions: {total}")
            sources.append({"type": "aggregate", "id": "sum_transactions_amount"})

        elif operation in ("max", "min"):
            order = Transaction.amount.desc() if operation == "max" else Transaction.amount.asc()
            rows = query.order_by(order).limit(intent["limit"]).all()
            label = "Highest" if operation == "max" else "Lowest"
            context_lines.append(f"{label} amount transaction(s):")
            for transaction in rows:
                context_lines.append(format_transaction(transaction))
                sources.append({"type": "transaction", "id": transaction.transaction_number})

        elif operation == "list":
            total = query.count()
            rows = (
                query.order_by(Transaction.id.desc())
                .limit(max_records)
                .all()
            )
            context_lines.append(
                f"Found {total} matching transactions (showing {len(rows)})."
            )
            for transaction in rows:
                context_lines.append(format_transaction(transaction))
                sources.append({"type": "transaction", "id": transaction.transaction_number})

    elif entity == "customer":
        query = db.query(Customer)

        if operation == "count":
            total = query.count()
            context_lines.append(f"Total number of customers: {total}")
            sources.append({"type": "aggregate", "id": "count_customers"})

        elif operation == "list":
            total = query.count()
            rows = query.order_by(Customer.id).limit(max_records).all()
            context_lines.append(
                f"Found {total} customers (showing {len(rows)})."
            )
            for customer in rows:
                context_lines.append(format_customer(customer))
                sources.append({"type": "customer", "id": customer.customer_number})

        # "sum" has no numeric field on Customer - fall through
        # with no results if asked, since there's nothing to sum.

    return context_lines[:max_records], sources[:max_records]


# =========================================================
# RETRIEVE CONTEXT (main entry point)
# =========================================================
# Returns a list of formatted context strings plus a
# lightweight "sources" list describing what was retrieved,
# so the API response can show what grounded the answer.

def retrieve_context(db: Session, question: str, max_records: int = 20):

    # --- Aggregate/list questions take priority -------------
    # ("how many accounts", "list all active accounts", etc.)
    # These don't reference a specific record, so check this
    # before falling back to exact-ID / name matching.

    aggregate_intent = detect_aggregate_intent(question)
    if aggregate_intent:
        context_lines, sources = retrieve_aggregate_context(
            db, question, aggregate_intent, max_records
        )
        if context_lines:
            return context_lines, sources
        # if aggregate detection matched but found nothing to
        # query (e.g. "sum of customers"), fall through to the
        # normal exact-match logic below as a safety net.

    entities = extract_entities(question)
    context_lines = []
    sources = []

    # --- Exact ID lookups -----------------------------------

    for customer_number in entities["customer_numbers"]:
        customer = (
            db.query(Customer)
            .filter(Customer.customer_number == customer_number)
            .first()
        )
        if customer:
            context_lines.append(format_customer(customer))
            sources.append({"type": "customer", "id": customer.customer_number})

            for account in customer.accounts:
                context_lines.append(format_account(account))
                sources.append({"type": "account", "id": account.account_number})

    for account_number in entities["account_numbers"]:
        account = (
            db.query(Account)
            .filter(Account.account_number == account_number)
            .first()
        )
        if account:
            context_lines.append(format_account(account))
            sources.append({"type": "account", "id": account.account_number})

            transactions = (
                db.query(Transaction)
                .filter(Transaction.account_number == account.account_number)
                .order_by(Transaction.id.desc())
                .limit(10)
                .all()
            )
            for transaction in transactions:
                context_lines.append(format_transaction(transaction))
                sources.append({"type": "transaction", "id": transaction.transaction_number})

    for transaction_number in entities["transaction_numbers"]:
        transaction = (
            db.query(Transaction)
            .filter(Transaction.transaction_number == transaction_number)
            .first()
        )
        if transaction:
            context_lines.append(format_transaction(transaction))
            sources.append({"type": "transaction", "id": transaction.transaction_number})

    # --- Email lookup ----------------------------------------

    for email in entities["emails"]:
        customer = (
            db.query(Customer)
            .filter(Customer.email == email)
            .first()
        )
        if customer:
            context_lines.append(format_customer(customer))
            sources.append({"type": "customer", "id": customer.customer_number})

    # --- Fallback: fuzzy name search --------------------------
    # If nothing matched by ID, try matching customer names
    # mentioned in the question (naive but useful for
    # "what's John Smith's balance?" style questions).

    if not context_lines:

        words = [w for w in re.findall(r"[A-Za-z]+", question) if len(w) > 2]

        if words:
            name_matches = (
                db.query(Customer)
                .filter(
                    or_(
                        *[Customer.first_name.ilike(f"%{w}%") for w in words],
                        *[Customer.last_name.ilike(f"%{w}%") for w in words],
                    )
                )
                .limit(5)
                .all()
            )

            for customer in name_matches:
                context_lines.append(format_customer(customer))
                sources.append({"type": "customer", "id": customer.customer_number})

                for account in customer.accounts:
                    context_lines.append(format_account(account))
                    sources.append({"type": "account", "id": account.account_number})

    return context_lines[:max_records], sources[:max_records]
