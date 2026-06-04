from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Notification(Base):
    __tablename__ = "notification"

    n_id = Column(Integer, primary_key=True, autoincrement=True)
    created_time = Column(TIMESTAMP, nullable=False)
    title = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(30))
    state_us = Column(String(20), nullable=False)
    u_id = Column(String(50), ForeignKey("pb_user.u_id"), nullable=False)
    s_id = Column(Integer, ForeignKey("pb_schedule.s_id"), nullable=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("s_id", "category", name="uq_notification_s_id_category"),
        CheckConstraint(
            "category IN ('방문 예정 브리핑', '거액 거래 탐지', '만기 알림', '이탈 위험', '안부 연락')",
            name="ck_notification_category",
        ),
    )

    # Relationships
    pb_user = relationship("PbUser")
    schedule = relationship("Schedule")
    customer = relationship("Customer")
