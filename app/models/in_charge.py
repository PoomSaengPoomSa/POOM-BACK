from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class InCharge(Base):
    __tablename__ = "in_charge"

    u_id = Column(String(50), ForeignKey("pb_user.u_id"), primary_key=True)
    c_id = Column(Integer, ForeignKey("customer.c_id"), primary_key=True)

    # Relationships
    pb_user = relationship("PbUser")
    customer = relationship("Customer")
