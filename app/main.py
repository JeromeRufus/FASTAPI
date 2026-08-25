from fastapi import FastAPI

from app.database import Base, engine

from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User

from app.router.customer import router as customer_router
from app.router.account import router as account_router
from app.router.transaction import router as transaction_router
from app.router.auth import router as auth_router

from app.exceptions.custom_exception import AppException
from app.exceptions.handlers import app_exception_handler


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(
    bind=engine
)


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Customer Account Management API",
    version="1.0.0"
)


# =========================================================
# GLOBAL EXCEPTION HANDLER
# =========================================================

app.add_exception_handler(
    AppException,
    app_exception_handler
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    customer_router
)

app.include_router(
    account_router
)

app.include_router(
    transaction_router
)

app.include_router(
    auth_router
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Customer Account Management API is running"
    }