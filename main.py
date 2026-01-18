# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from shared.database import engine

# Corrected Imports from Services
from services.identity.routes import users, auth
from services.pms.routes import records, hotel, check_in_out, rooms

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

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


# --- Startup: create tables ---
# --- Startup: create tables ---
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    print("Database tables managed by SQLModel.create_all()")    