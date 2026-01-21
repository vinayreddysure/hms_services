import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import records, hotel, check_in_out, rooms

app = FastAPI(title="PMS Service")

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

# --- Logging Middleware ---
from shared.middleware import LogExceptionMiddleware
app.add_middleware(LogExceptionMiddleware)

# --- Routers ---
app.include_router(records.router, prefix="/bookings", tags=["Records"])
app.include_router(hotel.router, prefix="/hotel", tags=["Hotel"]) 
app.include_router(check_in_out.router, prefix="/operations", tags=["Operations"]) 
app.include_router(rooms.router, prefix="/rooms", tags=["Rooms"]) 

@app.get("/health")
def health():
    return {"status": "ok", "service": "pms"}
