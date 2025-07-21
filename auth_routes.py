from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from datetime import datetime, timedelta
import hashlib
import random
import smtplib
import os
auth_router = APIRouter()
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")
# Hash password
def hash_pw(pw: str):
    return hashlib.sha256(pw.encode()).hexdigest()
# Send OTP via email
def send_otp_email(to_email: str, otp: str, purpose: str = "Login"):
    subject = f"Your OTP for Spin & Win App ({purpose})"
    body = f"Your One Time Password (OTP) is: {otp}\nIt is valid for 5 minutes."
    message = f"Subject: {subject}\n\n{body}"
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message)
    except Exception as e:
        raise HTTPException(500, f"Failed to send email: {str(e)}")
# :one: Send OTP for login
@auth_router.post("/send-otp")
def send_otp(email: str, db: Session = Depends(get_db)):
    if not email or "@" not in email:
        raise HTTPException(400, "Invalid email address")
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
    send_otp_email(email, otp, purpose="Login")
    return {"message": "OTP sent to your email."}
# :two: Verify OTP and Login
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
# :three: Forgot password - request OTP
@auth_router.post("/forgot-password-request")
def forgot_password_request(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=email).first()
    if not user:
        raise HTTPException(404, "Email not registered")
    otp = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)
    user.otp = otp
    user.otp_expiry = expiry
    db.commit()
    send_otp_email(email, otp, purpose="Password Reset")
    return {"message": "OTP sent to your email for password reset"}
# :four: Forgot password - confirm OTP and reset password
@auth_router.post("/forgot-password-confirm")
def forgot_password_confirm(email: str, otp: str, new_password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=email).first()
    if not user or user.otp != otp:
        raise HTTPException(401, "Invalid OTP")
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(401, "OTP expired")
    user.password_hash = hash_pw(new_password)
    user.otp = None
    user.otp_expiry = None
    db.commit()
    return {"message": "Password has been reset successfully."}
