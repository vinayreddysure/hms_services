from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, users

app = FastAPI(title="Identity Service")

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
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["hotelusers"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "identity"}
