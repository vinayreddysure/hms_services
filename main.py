# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from shared.database import engine
from shared.routes import users
from shared.routes import records
from shared.routes import hotel
from shared.routes import check_in_out
from shared.routes import rooms

from shared.routes import auth

app = FastAPI(title="My Backend API")

# --- CORS (so React/other frontend can call this) ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # add your frontend domain here in future
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["hotelusers"])
app.include_router(records.router, prefix="/bookings", tags=["Records"])
app.include_router(hotel.router, prefix="/hotel", tags=["Hotel"]) 
app.include_router(check_in_out.router, prefix="/operations", tags=["Operations"]) 
app.include_router(rooms.router, prefix="/rooms", tags=["Rooms"]) 


@app.get("/")
def root():
    return {"message": "Backend is running!"}


# --- Startup: create tables ---
# @app.on_event("startup")
# def on_startup():
#     # SQLModel.metadata.create_all(engine)
#     print("Database tables managed by Alembic")    