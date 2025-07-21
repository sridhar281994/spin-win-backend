from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from datetime import datetime, timedelta
import random
import smtplib
import os
auth_router = APIRouter()
# Load SMTP credentials from environment
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SMTP_EMAIL")  # your email address
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")  # your app-specific password
# Function to send OTP to email
def send_otp_email(to_email: str, otp: str):
    subject = "Your OTP for Spin & Win App"
    body = f"Your One Time Password (OTP) is: {otp}. It is valid for 5 minutes."
    message = f"Subject: {subject}\n\n{body}"
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, message)
# Route to send OTP
@auth_router.post("/send-otp")
def send_otp(email: str, db: Session = Depends(get_db)):
    otp = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)
    user = db.query(User).filter_by(username=email).first()
    if not user:
        user = User(username=email, otp=otp, otp_expiry=expiry, wallet_cents=0)
        db.add(user)
    else:
        user.otp = otp
        user.otp_expiry = expiry
    db.commit()
    try:
        send_otp_email(email, otp)
    except Exception as e:
        raise HTTPException(500, f"Failed to send OTP: {e}")
    return {"message": "OTP sent to your email"}
# Route to verify OTP
@auth_router.post("/verify-otp")
def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=email).first()
    if not user or user.otp != otp:
        raise HTTPException(401, "Invalid OTP")
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(401, "OTP expired")
    return {
        "status": "success",
        "user_id": user.id,
        "wallet": user.wallet_cents,
        "upi_id": user.upi_id,
    }
