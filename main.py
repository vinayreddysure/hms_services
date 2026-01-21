# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from shared.database import engine

# Corrected Imports from Services
from services.identity.routes import users, auth
from services.pms.routes import records, hotel, check_in_out, rooms

app = FastAPI(title="My Backend API")

# --- CORS (Configurable via Environment) ---
cors_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if cors_origins_str == "*":
    origins = ["*"]
    allow_credentials = False
else:
    origins = [o.strip() for o in cors_origins_str.split(",")]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
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
    
    # --- MANUAL MIGRATION PATCH ---
    # Since Alembic isn't running reliably, we force the column addition here.
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS address VARCHAR"))
            conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS city VARCHAR"))
            conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS state VARCHAR"))
            conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS zip_code VARCHAR"))
            
            # Also cleanup bookings while we are at it (Reset requested by user)
            # conn.execute(text("UPDATE bookings SET status = 'Completed', actual_check_out_at = NOW() WHERE status = 'Active'"))
            # conn.execute(text("UPDATE rooms SET status = 'A' WHERE status = 'O'"))
            
            conn.commit()
            print("MANUAL MIGRATION SUCCESS: Address columns added.")
        except Exception as e:
            print(f"Manual migration warning (might already exist): {e}")    