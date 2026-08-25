from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse
)

from app.services.account_service import (
    create_new_account,
    get_all_accounts,
    get_account,
    get_customer_accounts,
    update_account,
    delete_account
)


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)


# =========================================================
# CREATE ACCOUNT
# =========================================================

@router.post(
    "/",
    response_model=AccountResponse
)
@router.post(
    "/",
    response_model=AccountResponse
)
def create_account_api(
    account: AccountCreate,
    db: Session = Depends(get_db)
):

    return create_new_account(
        db=db,
        customer_number=account.customer_number,
        account_type=account.account_type,
        balance=account.balance
    )

    return result


# =========================================================
# GET ALL ACCOUNTS
# =========================================================

@router.get(
    "/",
    response_model=list[AccountResponse]
)
def get_accounts_api(
    db: Session = Depends(get_db)
):

    return get_all_accounts(db)


# =========================================================
# GET ACCOUNT BY ACCOUNT NUMBER
# =========================================================

@router.get(
    "/number/{account_number}",
    response_model=AccountResponse
)
def get_account_api(
    account_number: str,
    db: Session = Depends(get_db)
):

    return get_account(
        db=db,
        account_number=account_number
    )


# =========================================================
# GET ACCOUNTS BY CUSTOMER NUMBER
# =========================================================

@router.get(
    "/customer/{customer_number}",
    response_model=list[AccountResponse]
)
def get_customer_accounts_api(
    customer_number: str,
    db: Session = Depends(get_db)
):

    return get_customer_accounts(
        db=db,
        customer_number=customer_number
    )


# =========================================================
# UPDATE ACCOUNT
# =========================================================

@router.put(
    "/number/{account_number}",
    response_model=AccountResponse
)
def update_account_api(
    account_number: str,
    account: AccountCreate,
    db: Session = Depends(get_db)
):

    return update_account(
        db=db,
        account_number=account_number,
        account_type=account.account_type,
        balance=account.balance,
        status="ACTIVE"
    )


# =========================================================
# DELETE ACCOUNT
# =========================================================

@router.delete(
    "/number/{account_number}"
)
def delete_account_api(
    account_number: str,
    db: Session = Depends(get_db)
):

    delete_account(
        db=db,
        account_number=account_number
    )

    return {
        "message": "Account deleted successfully",
        "account_number": account_number
    }