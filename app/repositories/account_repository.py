import uuid

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.customer import Customer


# =========================================================
# CREATE ACCOUNT
# =========================================================

def create_account(
    db: Session,
    customer_number: str,
    account_type: str,
    balance
):

    # Check customer exists

    customer = (
        db.query(Customer)
        .filter(
            Customer.customer_number == customer_number
        )
        .first()
    )

    if customer is None:
        return None

    # Generate account number

    account_number = (
        "ACC" +
        uuid.uuid4().hex[:8].upper()
    )

    account = Account(
        account_number=account_number,
        customer_number=customer_number,
        account_type=account_type,
        balance=balance,
        status="ACTIVE"
    )

    db.add(account)

    db.commit()

    db.refresh(account)

    return account


# =========================================================
# GET ALL ACCOUNTS
# =========================================================

def get_accounts(db: Session):

    return (
        db.query(Account)
        .all()
    )


# =========================================================
# GET ACCOUNT BY ACCOUNT NUMBER
# =========================================================

def get_account_by_number(
    db: Session,
    account_number: str
):

    return (
        db.query(Account)
        .filter(
            Account.account_number == account_number
        )
        .first()
    )


# =========================================================
# GET ACCOUNTS BY CUSTOMER NUMBER
# =========================================================

def get_accounts_by_customer_number(
    db: Session,
    customer_number: str
):

    return (
        db.query(Account)
        .filter(
            Account.customer_number == customer_number
        )
        .all()
    )


# =========================================================
# UPDATE ACCOUNT
# =========================================================

def update_account_by_number(
    db,
    account_number: str,
    account_type: str,
    status: str,
    balance
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

    account.account_type = account_type
    account.balance = balance
    account.status = status

    db.commit()

    db.refresh(account)

    return account


# =========================================================
# DELETE ACCOUNT
# =========================================================

def delete_account_by_number(
    db: Session,
    account_number: str
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

    db.delete(account)

    db.commit()

    return account