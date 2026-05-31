from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    BigInteger,
    Boolean,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customer"

    c_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    number = Column(String(20), nullable=False)
    birthday = Column(Date)
    job = Column(String(50), default="무직")
    gender = Column(String(1))
    email = Column(String(50), nullable=False)
    address = Column(String(255), nullable=False)
    tendency = Column(String(30), nullable=False)
    total_assets = Column(BigInteger, nullable=False)
    deposit = Column(BigInteger, nullable=False)
    investment = Column(BigInteger, nullable=False)
    pension = Column(BigInteger, nullable=False)
    loan = Column(BigInteger, nullable=False)
    net_worth = Column(BigInteger, nullable=False)
    marital_status = Column(Boolean, nullable=False)
    start_date = Column(Date, default=func.current_date())
    grade = Column(String(30), nullable=False)
    llm_insight = Column(Text, nullable=True)
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    analysis_time = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F')", name="ck_customer_gender"),
        CheckConstraint(
            "tendency IN ('안정형', '안정추구형', '위험중립형', '적극투자형', '공격투자형')",
            name="ck_customer_tendency",
        ),
    )

    # Relationships
    relationships = relationship("CustomerRelationship", back_populates="customer")
    informations = relationship("CustomerInformation", back_populates="customer")
    accounts = relationship("CustomerAccount", back_populates="customer")
    transactions = relationship("CustomerTransaction", back_populates="customer")
    products = relationship("CustomerProduct", back_populates="customer")


class CustomerRelationship(Base):
    __tablename__ = "customer_relationship"

    cr_id = Column(Integer, primary_key=True, autoincrement=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    relationship_ = Column("relationship", String(50), nullable=False)
    information = Column(Text)

    # Relationships
    customer = relationship("Customer", back_populates="relationships")


class CustomerInformation(Base):
    __tablename__ = "customer_information"

    ci_id = Column(Integer, primary_key=True, autoincrement=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    category = Column(String(10), nullable=False)
    contents = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint(
            "category IN ('기호', '관계', '성향', '상품', '건강', '기타')",
            name="ck_customer_info_category",
        ),
    )

    # Relationships
    customer = relationship("Customer", back_populates="informations")
