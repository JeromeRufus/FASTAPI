from app.repositories.account_repository import (
    create_account,
    get_accounts,
    get_account_by_number,
    get_accounts_by_customer_number,
    update_account_by_number,
    delete_account_by_number
)

from app.exceptions.custom_exception import (
    AccountNotFoundException,
    CustomerNotFoundException
)


def create_new_account(
    db,
    customer_number,
    account_type,
    balance
):

    account = create_account(
        db=db,
        customer_number=customer_number,
        account_type=account_type,
        balance=balance
    )

    if account is None:
        raise CustomerNotFoundException(customer_number)

    return account


def get_all_accounts(db):

    return get_accounts(db)


def get_account(db, account_number):

    account = get_account_by_number(
        db=db,
        account_number=account_number
    )

    if not account:
        raise AccountNotFoundException(account_number)

    return account


def get_customer_accounts(
    db,
    customer_number
):

    return get_accounts_by_customer_number(
        db=db,
        customer_number=customer_number
    )


def update_account(
    db,
    account_number,
    account_type,
    balance,
    status
):

    account = get_account_by_number(
        db=db,
        account_number=account_number
    )

    if not account:
        raise AccountNotFoundException(account_number)

    return update_account_by_number(
        db=db,
        account_number=account_number,
        account_type=account_type,
        balance=balance,
        status=status
    )


def delete_account(
    db,
    account_number
):

    account = get_account_by_number(
        db=db,
        account_number=account_number
    )

    if not account:
        raise AccountNotFoundException(account_number)

    return delete_account_by_number(
        db=db,
        account_number=account_number
    )