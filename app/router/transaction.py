from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse
)

from app.services.transaction_service import (
    deposit,
    withdraw,
    get_all_transactions,
    get_transaction,
    get_account_transactions
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


# =========================================================
# DEPOSIT
# =========================================================

@router.post(
    "/deposit",
    response_model=TransactionResponse
)
def deposit_money(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):

    return deposit(
        db=db,
        account_number=transaction.account_number,
        amount=transaction.amount
    )


# =========================================================
# WITHDRAW
# =========================================================

@router.post(
    "/withdraw",
    response_model=TransactionResponse
)
def withdraw_money(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):

    return withdraw(
        db=db,
        account_number=transaction.account_number,
        amount=transaction.amount
    )


# =========================================================
# GET ALL TRANSACTIONS
# =========================================================

@router.get(
    "/",
    response_model=list[TransactionResponse]
)
def get_transactions_api(
    db: Session = Depends(get_db)
):

    return get_all_transactions(db)


# =========================================================
# GET TRANSACTION BY NUMBER
# =========================================================

@router.get(
    "/number/{transaction_number}",
    response_model=TransactionResponse
)
def get_transaction_by_number(
    transaction_number: str,
    db: Session = Depends(get_db)
):

    return get_transaction(
        db=db,
        transaction_number=transaction_number
    )


# =========================================================
# GET TRANSACTIONS BY ACCOUNT NUMBER
# =========================================================

@router.get(
    "/account/{account_number}",
    response_model=list[TransactionResponse]
)
def get_account_transaction_history(
    account_number: str,
    db: Session = Depends(get_db)
):

    return get_account_transactions(
        db=db,
        account_number=account_number
    )