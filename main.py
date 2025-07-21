from fastapi import FastAPI
from database import engine, Base
from auth_routes import auth_router
from transaction_routes import tx_router
from game_routes import game_router
Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(auth_router, prefix="/auth")
app.include_router(tx_router, prefix="/transaction")
app.include_router(game_router, prefix="/game")