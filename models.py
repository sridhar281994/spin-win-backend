from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, BigInteger, ForeignKey
from sqlalchemy.sql import func
from database import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)  # email or username
    password_hash = Column(String, nullable=False)
    upi_id = Column(String, nullable=False)
    wallet_cents = Column(BigInteger, default=0)
    is_active_in_stage = Column(Boolean, default=False)
    active_stage = Column(Integer, nullable=True)
    active_join_ts = Column(TIMESTAMP(timezone=True), server_default=func.now())
    otp = Column(String, nullable=True)  # stores OTP value
    otp_expiry = Column(TIMESTAMP(timezone=True), nullable=True)  # stores OTP expiry time
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_cents = Column(BigInteger)
    type = Column(String)  # recharge/withdraw
    status = Column(String, default="pending")
    ref = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
