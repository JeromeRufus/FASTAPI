import uuid

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction


# =========================================================
# CREATE DEPOSIT
# =========================================================

def create_deposit(
    db: Session,
    account_number: str,
    amount
):

    account = (
        db.query(Account)
        .filter(
            Account.account_number == account_number
        )
        .first()
    )

    if account is None:
        return None

    if amount <= 0:
        return "INVALID_AMOUNT"

    account.balance = account.balance + amount

    transaction_number = (
        "TXN"
        + uuid.uuid4().hex[:8].upper()
    )

    transaction = Transaction(
        transaction_number=transaction_number,
        account_number=account_number,
        transaction_type="DEPOSIT",
        amount=amount,
        balance_after=account.balance
    )

    db.add(transaction)

    db.commit()

    db.refresh(transaction)

    return transaction


# =========================================================
# CREATE WITHDRAWAL
# =========================================================

def create_withdrawal(
    db: Session,
    account_number: str,
    amount
):

    account = (
        db.query(Account)
        .filter(
            Account.account_number == account_number
        )
        .first()
    )

    if account is None:
        return None

    if amount <= 0:
        return "INVALID_AMOUNT"

    if account.balance < amount:
        return "INSUFFICIENT_BALANCE"

    account.balance = account.balance - amount

    transaction_number = (
        "TXN"
        + uuid.uuid4().hex[:8].upper()
    )

    transaction = Transaction(
        transaction_number=transaction_number,
        account_number=account_number,
        transaction_type="WITHDRAWAL",
        amount=amount,
        balance_after=account.balance
    )

    db.add(transaction)

    db.commit()

    db.refresh(transaction)

    return transaction


# =========================================================
# GET ALL TRANSACTIONS
# =========================================================

def get_transactions(
    db: Session
):

    return (
        db.query(Transaction)
        .order_by(
            Transaction.id.desc()
        )
        .all()
    )


# =========================================================
# GET TRANSACTION BY NUMBER
# =========================================================

def get_transaction_by_number(
    db: Session,
    transaction_number: str
):

    return (
        db.query(Transaction)
        .filter(
            Transaction.transaction_number
            == transaction_number
        )
        .first()
    )


# =========================================================
# GET TRANSACTIONS BY ACCOUNT
# =========================================================

def get_transactions_by_account(
    db: Session,
    account_number: str
):

    return (
        db.query(Transaction)
        .filter(
            Transaction.account_number
            == account_number
        )
        .order_by(
            Transaction.id.desc()
        )
        .all()
    )