from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ConsultationMemo(Base):
    __tablename__ = "consultation_memo"

    cm_id = Column(Integer, primary_key=True, autoincrement=True)
    consult_date = Column(DateTime, nullable=False)
    memo = Column(Text, nullable=False)
    c_id = Column(Integer, ForeignKey("customer.c_id"), nullable=False)
    u_id = Column(String(50), ForeignKey("pb_user.u_id"), nullable=False)

    # Relationships
    customer = relationship("Customer")
    pb_user = relationship("PbUser")
    report = relationship("ConsultationReport", back_populates="consultation_memo", uselist=False)


class ConsultationReport(Base):
    __tablename__ = "consultation_report"

    cr_id = Column(Integer, primary_key=True, autoincrement=True)
    key_contents = Column(Text, nullable=False)
    special_notes = Column(Text, nullable=False)
    follow_up_actions = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    cm_id = Column(Integer, ForeignKey("consultation_memo.cm_id"), nullable=False)

    # Relationships
    consultation_memo = relationship("ConsultationMemo", back_populates="report")
