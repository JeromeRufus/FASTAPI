from pydantic import BaseModel, EmailStr


# CREATE CUSTOMER
class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


# UPDATE CUSTOMER
class CustomerUpdate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


# CUSTOMER RESPONSE
class CustomerResponse(BaseModel):
    id: int
    customer_number: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str

    class Config:
        from_attributes = True