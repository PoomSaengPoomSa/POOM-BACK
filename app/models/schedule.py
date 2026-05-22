from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Schedule(Base):
    __tablename__ = "pb_schedule"

    s_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(50), nullable=False)
    memo = Column(String(80))
    category = Column(String(10))
    execution_date = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    u_id = Column(String(50), ForeignKey("pb_user.u_id"), nullable=False)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=True)
    at_id = Column(Integer, ForeignKey("ai_todo.at_id"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "category IN ('개인', '공지', '상담')",
            name="ck_schedule_category",
        ),
    )

    # Relationships
    pb_user = relationship("PbUser")
    customer = relationship("Customer")
    ai_todo = relationship("AiTodo")
