from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Branch(Base):
    __tablename__ = "branch"

    b_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    region = Column(String(50), nullable=False)
    b_phone = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)

    # Relationships
    pb_users = relationship("PbUser", back_populates="branch_rel")
