from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Account(Base):

    __tablename__ = "accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    account_number = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    customer_number = Column(
        String(20),
        ForeignKey("customers.customer_number"),
        nullable=False,
        index=True
    )

    account_type = Column(
        String(20),
        nullable=False
    )

    balance = Column(
        Numeric(15, 2),
        default=0.00,
        nullable=False
    )

    status = Column(
        String(20),
        default="ACTIVE",
        nullable=False
    )

    customer = relationship(
        "Customer",
        back_populates="accounts"
    )