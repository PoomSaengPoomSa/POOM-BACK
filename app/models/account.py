from sqlalchemy import Column, Integer, String, Date, ForeignKey, LargeBinary, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Account(Base):
    __tablename__ = "account"

    id = Column(String(50), primary_key=True)
    password = Column(String(255), nullable=False)
    role = Column(String(30), default="user")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="ck_account_role"),
    )

    # Relationships
    pb_user = relationship("PbUser", back_populates="account", uselist=False)


class PbUser(Base):
    __tablename__ = "pb_user"

    u_id = Column(String(50), ForeignKey("account.id"), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    number = Column(String(20), nullable=False)
    branch = Column("branch", Integer, ForeignKey("branch.b_id"), nullable=False)
    status = Column(String(20), default="재직")
    position = Column(String(30), default="PB")
    profile = Column(LargeBinary)
    start_date = Column(Date, nullable=False)
    birth_date = Column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('재직', '휴직', '퇴사', '발령대기')",
            name="ck_pb_user_status",
        ),
        CheckConstraint(
            "position IN ('PB', '팀장', '지점장')",
            name="ck_pb_user_position",
        ),
    )

    # Relationships
    account = relationship("Account", back_populates="pb_user")
    branch_rel = relationship("Branch", back_populates="pb_users")
