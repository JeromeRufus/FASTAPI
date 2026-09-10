import re

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.query_helpers import distinct_values


# =========================================================
# EXACT ID / EMAIL EXTRACTION
# =========================================================
# Your IDs follow predictable prefixes (CUST/ACC/TXN + 8 hex
# chars). This fast path catches "what's the balance on
# ACC1234ABCD" style questions without needing an extra LLM
# call - cheaper and faster than the intent-classification
# path below, which only runs if this finds nothing.

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
# FAST PATH: EXACT ID / EMAIL LOOKUP
# =========================================================

def retrieve_exact_context(db: Session, question: str, max_records: int = 20):

    entities = extract_entities(question)
    context_lines = []
    sources = []

    for customer_number in entities["customer_numbers"]:
        customer = db.query(Customer).filter(Customer.customer_number == customer_number).first()
        if customer:
            context_lines.append(format_customer(customer))
            sources.append({"type": "customer", "id": customer.customer_number})
            for account in customer.accounts:
                context_lines.append(format_account(account))
                sources.append({"type": "account", "id": account.account_number})

    for account_number in entities["account_numbers"]:
        account = db.query(Account).filter(Account.account_number == account_number).first()
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

    for email in entities["emails"]:
        customer = db.query(Customer).filter(Customer.email == email).first()
        if customer:
            context_lines.append(format_customer(customer))
            sources.append({"type": "customer", "id": customer.customer_number})

    return context_lines[:max_records], sources[:max_records]


# =========================================================
# GENERIC PATH: LLM-CLASSIFIED INTENT EXECUTOR
# =========================================================
# `intent` comes from intent_service.extract_intent() - a JSON
# query plan Gemini produced from the raw question. This just
# executes whatever it describes; it doesn't need to know about
# specific phrasings at all, which is the point.

def retrieve_context_from_intent(db: Session, intent: dict, max_records: int = 20):

    context_lines = []
    sources = []

    entity = intent.get("entity")
    operation = intent.get("operation")
    limit = intent.get("limit") or max_records

    if entity == "account":
        query = db.query(Account)

        if intent.get("account_number"):
            query = query.filter(Account.account_number == intent["account_number"].upper())
        if intent.get("customer_number"):
            query = query.filter(Account.customer_number == intent["customer_number"].upper())
        if intent.get("account_types"):
            query = query.filter(Account.account_type.in_(intent["account_types"]))
        if intent.get("statuses"):
            query = query.filter(Account.status.in_(intent["statuses"]))
        if intent.get("balance_gt") is not None:
            query = query.filter(Account.balance > intent["balance_gt"])
        if intent.get("balance_lt") is not None:
            query = query.filter(Account.balance < intent["balance_lt"])

        if operation == "count":
            total = query.count()
            context_lines.append(f"Total number of accounts matching the filters: {total}")
            sources.append({"type": "aggregate", "id": "count_accounts"})

        elif operation == "sum":
            total = query.with_entities(func.sum(Account.balance)).scalar() or 0
            context_lines.append(f"Sum of balances for matching accounts: {total}")
            sources.append({"type": "aggregate", "id": "sum_accounts_balance"})

        elif operation in ("max", "min"):
            order = Account.balance.desc() if operation == "max" else Account.balance.asc()
            rows = query.order_by(order).limit(intent.get("limit") or 1).all()
            label = "Highest" if operation == "max" else "Lowest"
            context_lines.append(f"{label} balance account(s):")
            for account in rows:
                context_lines.append(format_account(account))
                sources.append({"type": "account", "id": account.account_number})

        elif operation == "distinct":
            field = intent.get("distinct_field") or "account_type"
            column = Account.status if field == "status" else Account.account_type
            values = distinct_values(db, column)
            context_lines.append(
                f"Distinct account {field} values in use: "
                f"{', '.join(values) if values else 'none found'}"
            )
            sources.append({"type": "aggregate", "id": f"distinct_account_{field}"})

        else:  # "lookup" / "list" / fallback
            total = query.count()
            rows = query.order_by(Account.id).limit(limit).all()
            context_lines.append(f"Found {total} matching accounts (showing {len(rows)}).")
            for account in rows:
                context_lines.append(format_account(account))
                sources.append({"type": "account", "id": account.account_number})

    elif entity == "transaction":
        query = db.query(Transaction)

        if intent.get("transaction_number"):
            query = query.filter(Transaction.transaction_number == intent["transaction_number"].upper())
        if intent.get("account_number"):
            query = query.filter(Transaction.account_number == intent["account_number"].upper())
        if intent.get("transaction_types"):
            query = query.filter(Transaction.transaction_type.in_(intent["transaction_types"]))
        if intent.get("amount_gt") is not None:
            query = query.filter(Transaction.amount > intent["amount_gt"])
        if intent.get("amount_lt") is not None:
            query = query.filter(Transaction.amount < intent["amount_lt"])

        if operation == "count":
            total = query.count()
            context_lines.append(f"Total number of transactions matching the filters: {total}")
            sources.append({"type": "aggregate", "id": "count_transactions"})

        elif operation == "sum":
            total = query.with_entities(func.sum(Transaction.amount)).scalar() or 0
            context_lines.append(f"Sum of amounts for matching transactions: {total}")
            sources.append({"type": "aggregate", "id": "sum_transactions_amount"})

        elif operation in ("max", "min"):
            order = Transaction.amount.desc() if operation == "max" else Transaction.amount.asc()
            rows = query.order_by(order).limit(intent.get("limit") or 1).all()
            label = "Highest" if operation == "max" else "Lowest"
            context_lines.append(f"{label} amount transaction(s):")
            for transaction in rows:
                context_lines.append(format_transaction(transaction))
                sources.append({"type": "transaction", "id": transaction.transaction_number})

        elif operation == "distinct":
            values = distinct_values(db, Transaction.transaction_type)
            context_lines.append(
                f"Distinct transaction type values in use: "
                f"{', '.join(values) if values else 'none found'}"
            )
            sources.append({"type": "aggregate", "id": "distinct_transaction_type"})

        else:  # "lookup" / "list" / fallback
            total = query.count()
            rows = query.order_by(Transaction.id.desc()).limit(limit).all()
            context_lines.append(f"Found {total} matching transactions (showing {len(rows)}).")
            for transaction in rows:
                context_lines.append(format_transaction(transaction))
                sources.append({"type": "transaction", "id": transaction.transaction_number})

    elif entity == "customer":
        query = db.query(Customer)

        if intent.get("customer_number"):
            query = query.filter(Customer.customer_number == intent["customer_number"].upper())
        if intent.get("email"):
            query = query.filter(Customer.email == intent["email"])
        if intent.get("name_contains"):
            name = intent["name_contains"]
            query = query.filter(
                or_(
                    Customer.first_name.ilike(f"%{name}%"),
                    Customer.last_name.ilike(f"%{name}%"),
                )
            )

        if operation == "count":
            total = query.count()
            context_lines.append(f"Total number of customers matching the filters: {total}")
            sources.append({"type": "aggregate", "id": "count_customers"})

        else:  # "lookup" / "list" / fallback
            total = query.count()
            rows = query.order_by(Customer.id).limit(limit).all()
            context_lines.append(f"Found {total} matching customers (showing {len(rows)}).")
            for customer in rows:
                context_lines.append(format_customer(customer))
                sources.append({"type": "customer", "id": customer.customer_number})
                for account in customer.accounts:
                    context_lines.append(format_account(account))
                    sources.append({"type": "account", "id": account.account_number})

    return context_lines[:max_records], sources[:max_records]