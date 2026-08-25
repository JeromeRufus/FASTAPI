from app.repositories.transaction_repository import (
    create_deposit,
    create_withdrawal,
    get_transactions,
    get_transaction_by_number,
    get_transactions_by_account
)

from app.exceptions.custom_exception import (
    AccountNotFoundException,
    TransactionNotFoundException,
    InvalidAmountException,
    InsufficientBalanceException
)


# =========================================================
# DEPOSIT
# =========================================================

def deposit(
    db,
    account_number,
    amount
):

    result = create_deposit(
        db=db,
        account_number=account_number,
        amount=amount
    )

    # Account not found
    if result is None:
        raise AccountNotFoundException(
            account_number
        )

    # Invalid amount
    if result == "INVALID_AMOUNT":
        raise InvalidAmountException()

    return result


# =========================================================
# WITHDRAW
# =========================================================

def withdraw(
    db,
    account_number,
    amount
):

    result = create_withdrawal(
        db=db,
        account_number=account_number,
        amount=amount
    )

    # Account not found
    if result is None:
        raise AccountNotFoundException(
            account_number
        )

    # Invalid amount
    if result == "INVALID_AMOUNT":
        raise InvalidAmountException()

    # Insufficient balance
    if result == "INSUFFICIENT_BALANCE":
        raise InsufficientBalanceException()

    return result


# =========================================================
# GET ALL TRANSACTIONS
# =========================================================

def get_all_transactions(db):

    return get_transactions(db)


# =========================================================
# GET TRANSACTION BY NUMBER
# =========================================================

def get_transaction(
    db,
    transaction_number
):

    transaction = get_transaction_by_number(
        db=db,
        transaction_number=transaction_number
    )

    # Transaction not found
    if transaction is None:
        raise TransactionNotFoundException(
            transaction_number
        )

    return transaction


# =========================================================
# GET TRANSACTIONS BY ACCOUNT
# =========================================================

def get_account_transactions(
    db,
    account_number
):

    return get_transactions_by_account(
        db=db,
        account_number=account_number
    )