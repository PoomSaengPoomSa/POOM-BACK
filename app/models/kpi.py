from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    Date,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Kpi(Base):
    __tablename__ = "kpi"

    kpi_id = Column(Integer, primary_key=True, autoincrement=True)
    aum = Column(BigInteger, nullable=False)
    non_interest = Column(BigInteger, nullable=False)
    new_customer = Column(BigInteger, nullable=False, default=0)
    kpi_type = Column(String(20), nullable=False)
    u_id = Column(String(50), ForeignKey("pb_user.u_id"), nullable=True)
    b_id = Column(Integer, ForeignKey("branch.b_id"), nullable=True)
    created_date = Column(Date, default=func.current_date())
    target_aum = Column(BigInteger, nullable=False)
    target_non_interest = Column(BigInteger, nullable=False)
    target_new_customer = Column(BigInteger, nullable=False, default=0)
    current_aum = Column(BigInteger, nullable=False)
    current_non_interest = Column(BigInteger, nullable=False)
    current_new_customer = Column(BigInteger, nullable=False)
    recorded_date = Column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "kpi_type IN ('PB', 'BRANCH')",
            name="ck_kpi_type",
        ),
    )

    # Relationships
    pb_user = relationship("PbUser")
    branch = relationship("Branch")
