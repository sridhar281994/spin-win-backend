from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, Transaction
from database import get_db
import os
from dotenv import load_dotenv
load_dotenv()
tx_router = APIRouter()
ADMIN_UPI_ID = os.getenv("ADMIN_UPI_ID")
@tx_router.post("/recharge")
def create_recharge(user_id: int, amount: int, db: Session = Depends(get_db)):
    """
    Step 1: Create a recharge intent.
    Step 2: Return a UPI intent URL to open in Android app.
    """
    if amount < 1:
        raise HTTPException(400, "Minimum ₹1 required")
    txn = Transaction(
        user_id=user_id,
        amount_cents=amount * 100,
        type="recharge",
        status="pending",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    upi_url = (
        f"upi://pay?pa={ADMIN_UPI_ID}&pn=SpinAndWin&am={amount}&cu=INR"
        f"&tn=Recharge_{txn.id}"
    )
    return {
        "transaction_id": txn.id,
        "upi_url": upi_url,
        "message": f"Please complete UPI payment of ₹{amount}",
    }
@tx_router.post("/confirm-recharge")
def confirm_recharge(user_id: int, transaction_id: int, db: Session = Depends(get_db)):
    """
    This would be manually or semi-automatically called after verifying UPI txn
    """
    txn = db.query(Transaction).filter_by(id=transaction_id, user_id=user_id, type="recharge").first()
    if not txn:
        raise HTTPException(404, "Transaction not found")
    if txn.status == "success":
        return {"message": "Already confirmed"}
    # Mark as success and update wallet
    txn.status = "success"
    user = db.query(User).filter_by(id=user_id).first()
    user.wallet_cents += txn.amount_cents
    db.commit()
    return {"message": "Recharge confirmed", "wallet": user.wallet_cents // 100}
@tx_router.post("/withdraw")
def request_withdraw(user_id: int, amount: int, db: Session = Depends(get_db)):
    """
    Allows user to request withdraw from winnings.
    Admin will process payout manually or via payout API.
    """
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.wallet_cents < amount * 100:
        raise HTTPException(400, "Insufficient balance")
    # Deduct immediately
    user.wallet_cents -= amount * 100
    txn = Transaction(
        user_id=user_id,
        amount_cents=amount * 100,
        type="withdraw",
        status="pending"
    )
    db.add(txn)
    db.commit()
    return {
        "message": f"Withdrawal of ₹{amount} requested. It will be processed soon.",
        "wallet": user.wallet_cents // 100
    }
  @tx_router.get("/wallet")
def get_wallet_balance(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "wallet_rupees": user.wallet_cents // 100,
        "wallet_paise": user.wallet_cents % 100,
        "upi_id": user.upi_id
    }
