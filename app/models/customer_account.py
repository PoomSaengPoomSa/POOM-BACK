from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CustomerAccount(Base):
    __tablename__ = "customer_account"

    ca_id = Column(Integer, primary_key=True, autoincrement=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    account_num = Column(String(30), nullable=False)
    account_type = Column(String(20), nullable=False)
    balance = Column(Numeric(15, 2), nullable=False)
    opening_date = Column(DateTime, default=func.now())
    cu_id = Column(Integer, ForeignKey("customer_product.cu_id"), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "account_type IN ('보통', '예적금', '연금보험', '대출', '투자상품')",
            name="ck_customer_account_type",
        ),
    )

    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    customer_product = relationship("CustomerProduct", back_populates="customer_accounts")
    transactions = relationship("CustomerTransaction", back_populates="customer_account")


class CustomerTransaction(Base):
    __tablename__ = "customer_transaction"

    ct_id = Column(Integer, primary_key=True, autoincrement=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    ca_id = Column(Integer, ForeignKey("customer_account.ca_id"), nullable=False)
    ct_type = Column(String(1))
    amount = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)
    ct_datetime = Column(DateTime, nullable=False, default=func.now())
    briefs = Column(String(50))
    opp_name = Column(String(10), nullable=False)
    opp_account = Column(String(30), nullable=False)
    opp_bank_name = Column(String(10), nullable=False)
    channel = Column(String(20))

    __table_args__ = (
        CheckConstraint("ct_type IN ('D', 'W')", name="ck_transaction_type"),
        CheckConstraint(
            "channel IN ('ATM', 'MOBILE', 'BRANCH')",
            name="ck_transaction_channel",
        ),
    )

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    customer_account = relationship("CustomerAccount", back_populates="transactions")
