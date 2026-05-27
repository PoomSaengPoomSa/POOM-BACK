from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class InCharge(Base):
    __tablename__ = "in_charge"

    u_id = Column(String(50), ForeignKey("pb_user.u_id"), primary_key=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), primary_key=True)

    __table_args__ = (
        Index('idx_ic_cid', 'c_id'),
    )

    # Relationships
    pb_user = relationship("PbUser")
    customer = relationship("Customer")
