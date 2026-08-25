from pydantic import BaseModel
from decimal import Decimal


class TransactionCreate(BaseModel):

    account_number: str
    amount: Decimal


class TransactionResponse(BaseModel):

    id: int
    transaction_number: str
    account_number: str
    transaction_type: str
    amount: Decimal
    balance_after: Decimal

    class Config:
        from_attributes = True