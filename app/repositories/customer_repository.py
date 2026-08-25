from sqlalchemy.orm import Session

from app.models.customer import Customer


# =========================================================
# CREATE CUSTOMER
# =========================================================

def create_customer(
    db: Session,
    first_name: str,
    last_name: str,
    email: str,
    phone: str
):

    # Check duplicate email
    email_exists = (
        db.query(Customer)
        .filter(Customer.email == email)
        .first()
    )

    if email_exists:
        return "EMAIL_EXISTS"

    # Check duplicate phone
    phone_exists = (
        db.query(Customer)
        .filter(Customer.phone == phone)
        .first()
    )

    if phone_exists:
        return "PHONE_EXISTS"

    # Generate customer number
    import uuid

    customer_number = "CUST" + uuid.uuid4().hex[:8].upper()

    customer = Customer(
        customer_number=customer_number,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# =========================================================
# GET ALL CUSTOMERS
# =========================================================

def get_customers(db: Session):

    return (
        db.query(Customer)
        .all()
    )


# =========================================================
# GET CUSTOMER BY DATABASE ID
# =========================================================

def get_customer_by_id(
    db: Session,
    customer_id: int
):

    return (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )


# =========================================================
# GET CUSTOMER BY CUSTOMER NUMBER
# =========================================================

def get_customer_by_number(
    db: Session,
    customer_number: str
):

    return (
        db.query(Customer)
        .filter(
            Customer.customer_number == customer_number
        )
        .first()
    )


# =========================================================
# UPDATE CUSTOMER BY CUSTOMER NUMBER
# =========================================================

def update_customer_by_number(
    db: Session,
    customer_number: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str
):

    customer = (
        db.query(Customer)
        .filter(
            Customer.customer_number == customer_number
        )
        .first()
    )

    # Customer not found
    if customer is None:
        return None

    # Check email belongs to another customer
    email_exists = (
        db.query(Customer)
        .filter(
            Customer.email == email,
            Customer.customer_number != customer_number
        )
        .first()
    )

    if email_exists:
        return "EMAIL_EXISTS"

    # Check phone belongs to another customer
    phone_exists = (
        db.query(Customer)
        .filter(
            Customer.phone == phone,
            Customer.customer_number != customer_number
        )
        .first()
    )

    if phone_exists:
        return "PHONE_EXISTS"

    # Update fields
    customer.first_name = first_name
    customer.last_name = last_name
    customer.email = email
    customer.phone = phone

    db.commit()
    db.refresh(customer)

    return customer


# =========================================================
# DELETE CUSTOMER BY CUSTOMER NUMBER
# =========================================================

def delete_customer_by_number(
    db: Session,
    customer_number: str
):

    customer = (
        db.query(Customer)
        .filter(
            Customer.customer_number == customer_number
        )
        .first()
    )

    # Customer not found
    if customer is None:
        return None

    db.delete(customer)
    db.commit()

    return customer