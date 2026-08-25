from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse
)

from app.services.customer_service import (
    create_new_customer,
    get_all_customers,
    get_customer,
    get_customer_number,
    update_customer,
    delete_customer
)

from app.security.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


# =========================================================
# CREATE CUSTOMER
# =========================================================

@router.post(
    "/",
    response_model=CustomerResponse
)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = create_new_customer(
        db=db,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        phone=customer.phone
    )

    if result == "EMAIL_EXISTS":
        raise HTTPException(
            status_code=400,
            detail="Customer with this email already exists"
        )

    if result == "PHONE_EXISTS":
        raise HTTPException(
            status_code=400,
            detail="Customer with this phone number already exists"
        )

    return result


# =========================================================
# GET ALL CUSTOMERS
# =========================================================

@router.get(
    "/",
    response_model=list[CustomerResponse]
)
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return get_all_customers(db)


# =========================================================
# GET CUSTOMER BY DATABASE ID
# =========================================================

@router.get(
    "/id/{customer_id}",
    response_model=CustomerResponse
)
def get_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = get_customer(
        db=db,
        customer_id=customer_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return result


# =========================================================
# GET CUSTOMER BY CUSTOMER NUMBER
# =========================================================

@router.get(
    "/number/{customer_number}",
    response_model=CustomerResponse
)
def get_customer_by_number(
    customer_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = get_customer_number(
        db=db,
        customer_number=customer_number
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return result


# =========================================================
# UPDATE CUSTOMER BY CUSTOMER NUMBER
# =========================================================

@router.put(
    "/number/{customer_number}",
    response_model=CustomerResponse
)
def update_customer_by_number(
    customer_number: str,
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = update_customer(
        db=db,
        customer_number=customer_number,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        phone=customer.phone
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    if result == "EMAIL_EXISTS":
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    if result == "PHONE_EXISTS":
        raise HTTPException(
            status_code=400,
            detail="Phone number already exists"
        )

    return result


# =========================================================
# DELETE CUSTOMER BY CUSTOMER NUMBER
# =========================================================

@router.delete(
    "/number/{customer_number}"
)
def delete_customer_by_number(
    customer_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = delete_customer(
        db=db,
        customer_number=customer_number
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return {
        "message": "Customer deleted successfully",
        "customer_number": customer_number
    }   