from decimal import Decimal

from pydantic import BaseModel, Field


# =========================================================
# CREATE ACCOUNT
# =========================================================

class AccountCreate(BaseModel):

    customer_number: str

    account_type: str

    balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=0
    )


class AccountUpdate(BaseModel):
    account_type: str
    balance: Decimal
    status: str


# =========================================================
# ACCOUNT RESPONSE
# =========================================================

class AccountResponse(BaseModel):

    id: int

    account_number: str

    customer_number: str

    account_type: str

    balance: Decimal

    status: str

    class Config:
        from_attributes = True