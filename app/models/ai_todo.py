from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    CheckConstraint,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AiTodo(Base):
    __tablename__ = "ai_todo"

    at_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(50), nullable=False)
    memo = Column(String(80))
    category = Column(String(30))
    create_date = Column(TIMESTAMP, nullable=False)
    execution_date = Column(DateTime, nullable=False)
    is_checked = Column(Boolean, default=False)
    u_id = Column(String(50), ForeignKey("pb_user.u_id"), nullable=False)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "category IN ('KPI 기반', '상담 일정 제안', '안부 연락 제안', '신규 상품 분석')",
            name="ck_ai_todo_category",
        ),
    )

    # Relationships
    pb_user = relationship("PbUser")
    customer = relationship("Customer")
