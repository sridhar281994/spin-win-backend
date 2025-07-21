from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
import hashlib
auth_router = APIRouter()
def hash_pw(pw: str):
    return hashlib.sha256(pw.encode()).hexdigest()
@auth_router.post("/register")
def register(username: str, password: str, upi_id: str, db: Session = Depends(get_db)):
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(400, "Username exists")
    hashed_pw = hash_pw(password)
    user = User(username=username, password_hash=hashed_pw, upi_id=upi_id)
    db.add(user)
    db.commit()
    return {"status": "registered"}
@auth_router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    hashed_pw = hash_pw(password)
    user = db.query(User).filter_by(username=username, password_hash=hashed_pw).first()
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return {
        "status": "success",
        "user_id": user.id,
        "wallet": user.wallet_cents,
        "upi_id": user.upi_id
    }
