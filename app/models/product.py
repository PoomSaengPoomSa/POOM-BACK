from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    Boolean,
    Float,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    __tablename__ = "product"

    pd_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    explanation = Column(Text, nullable=False)
    type = Column(String(15), nullable=False)
    is_main = Column(Boolean, default=False)
    update_date = Column(Date, nullable=False)
    season = Column(String(20), nullable=False)
    issuer = Column(String(50), nullable=False)
    features = Column(Text, nullable=False)
    target_customer = Column(Text, nullable=False)
    expected_return = Column(Float, nullable=False)
    return_type = Column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "type IN ('보통', '예적금', '연금보험', '대출', '투자상품')",
            name="ck_product_type",
        ),
    )

    # Relationships
    customer_products = relationship("CustomerProduct", back_populates="product")


class CustomerProduct(Base):
    __tablename__ = "customer_product"

    cu_id = Column(Integer, primary_key=True, autoincrement=True)
    opening_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    pd_id = Column(Integer, ForeignKey("product.pd_id"), nullable=False)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="customer_products")
    customer = relationship("Customer", back_populates="products")
    customer_accounts = relationship("CustomerAccount", back_populates="customer_product")


class ProductMatching(Base):
    __tablename__ = "product_matching"

    matching_id = Column(Integer, primary_key=True, autoincrement=True)
    pd_id = Column(Integer, ForeignKey("product.pd_id"), nullable=False)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    is_suitable = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=False)
    created_date = Column(TIMESTAMP, nullable=False, default=func.now())

    # Relationships
    product = relationship("Product")
    customer = relationship("Customer")
