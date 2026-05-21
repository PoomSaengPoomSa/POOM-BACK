from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ChurnLevel(Base):
    __tablename__ = "churn_level"

    level_id = Column(Integer, primary_key=True, autoincrement=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    grade = Column(String(5))
    reason = Column(String(100), nullable=False)
    created_date = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint(
            "grade IN ('양호', '주의', '위험')",
            name="ck_churn_level_grade",
        ),
    )

    # Relationships
    customer = relationship("Customer")
