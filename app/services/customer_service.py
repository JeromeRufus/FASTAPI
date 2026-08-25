from app.repositories.customer_repository import (
    create_customer,
    get_customers,
    get_customer_by_id,
    get_customer_by_number,
    update_customer_by_number,
    delete_customer_by_number
)


def create_new_customer(
    db,
    first_name,
    last_name,
    email,
    phone
):
    return create_customer(
        db=db,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone
    )


def get_all_customers(db):
    return get_customers(db)


def get_customer(db, customer_id):
    return get_customer_by_id(
        db=db,
        customer_id=customer_id
    )


def get_customer_number(db, customer_number):
    return get_customer_by_number(
        db=db,
        customer_number=customer_number
    )


def update_customer(
    db,
    customer_number,
    first_name,
    last_name,
    email,
    phone
):
    return update_customer_by_number(
        db=db,
        customer_number=customer_number,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone
    )


def delete_customer(db, customer_number):
    return delete_customer_by_number(
        db=db,
        customer_number=customer_number
    )