from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):

    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    transaction_number = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    account_number = Column(
        String,
        nullable=False,
        index=True
    )

    transaction_type = Column(
        String,
        nullable=False
    )

    amount = Column(
        Numeric(15, 2),
        nullable=False
    )

    balance_after = Column(
        Numeric(15, 2),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )