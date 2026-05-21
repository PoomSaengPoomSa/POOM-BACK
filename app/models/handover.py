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


class Handover(Base):
    __tablename__ = "handover"

    h_id = Column(Integer, primary_key=True, autoincrement=True)
    a_id = Column(String(50), ForeignKey("account.id"), nullable=False)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    from_u_id = Column(String(50), ForeignKey("pb_user.u_id"), nullable=False)
    to_u_id = Column(String(50), ForeignKey("pb_user.u_id"), nullable=False)
    status = Column(String(20), default="대기")
    h_date = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('대기', '진행중', '완료')",
            name="ck_handover_status",
        ),
    )

    # Relationships
    account = relationship("Account")
    customer = relationship("Customer")
    from_user = relationship("PbUser", foreign_keys=[from_u_id])
    to_user = relationship("PbUser", foreign_keys=[to_u_id])
