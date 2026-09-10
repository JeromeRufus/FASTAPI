import re

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction


# =========================================================
# ENTITY EXTRACTION
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
# RETRIEVE CONTEXT
# =========================================================
# Returns a list of formatted context strings plus a
# lightweight "sources" list describing what was retrieved,
# so the API response can show what grounded the answer.

def retrieve_context(db: Session, question: str, max_records: int = 20):

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
