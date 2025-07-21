from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from datetime import datetime
import random
game_router = APIRouter()
# Define max players per stage
STAGE_CONFIG = {
    1: {"entry_fee": 100, "players_required": 2, "payout": 200},  # ₹1
    2: {"entry_fee": 200, "players_required": 2, "payout": 400},  # ₹2
    3: {"entry_fee": 500, "players_required": 2, "payout": 800},  # ₹5
    4: {"entry_fee": 500, "players_required": 10, "payout": 1200},  # Final stage
}
@game_router.post("/enter-stage")
def enter_stage(user_id: int, stage: int, db: Session = Depends(get_db)):
    if stage not in STAGE_CONFIG:
        raise HTTPException(400, "Invalid stage")
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    config = STAGE_CONFIG[stage]
    if user.wallet_cents < config["entry_fee"]:
        raise HTTPException(400, "Insufficient wallet balance")
    if user.is_active_in_stage:
        raise HTTPException(400, "User already active in a stage")
    # Deduct entry fee and mark user as active
    user.wallet_cents -= config["entry_fee"]
    user.is_active_in_stage = True
    user.active_stage = stage
    user.active_join_ts = datetime.utcnow()
    db.commit()
    return {"message": f"Joined Stage {stage}", "wallet": user.wallet_cents // 100}
@game_router.get("/match-status")
def match_status(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user or not user.is_active_in_stage:
        return {"matched": False}
    stage = user.active_stage
    config = STAGE_CONFIG.get(stage)
    if not config:
        return {"matched": False}
    # Find other users waiting in this stage
    players = db.query(User).filter_by(
        is_active_in_stage=True, active_stage=stage
    ).order_by(User.active_join_ts).limit(config["players_required"]).all()
    if len(players) < config["players_required"]:
        return {"matched": False, "waiting_for": config["players_required"] - len(players)}
    # Enough players found → select winner
    winner = random.choice(players)
    winner.wallet_cents += config["payout"]
    # Reset active state for all matched users
    for p in players:
        p.is_active_in_stage = False
        p.active_stage = None
        p.active_join_ts = None
    db.commit()
    return {
        "matched": True,
        "winner_id": winner.id,
        "payout_rupees": config["payout"] // 100,
        "wallet": winner.wallet_cents // 100,
        "players": [p.username for p in players]
    }
