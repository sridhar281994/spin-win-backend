from fastapi import FastAPI
from database import engine, Base
from auth_routes import auth_router
from transaction_routes import tx_router
from game_routes import game_router  # optional if game_routes.py exists
Base.metadata.create_all(bind=engine)
# :white_check_mark: define the app before using it
app = FastAPI()
@app.get("/")
def root():
    return {"message": "Backend is running"}
# :white_check_mark: include routers after app is defined
app.include_router(auth_router, prefix="/auth")
app.include_router(tx_router, prefix="/transaction")
app.include_router(game_router, prefix="/game")  # optional
