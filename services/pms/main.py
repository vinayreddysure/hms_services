from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import records, hotel, check_in_out, rooms

app = FastAPI(title="PMS Service")

# --- CORS ---
origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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
