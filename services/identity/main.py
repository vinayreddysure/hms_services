import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, users

app = FastAPI(title="Identity Service")

# --- CORS (Configurable via Environment) ---
# Set ALLOWED_ORIGINS in Railway: "https://your-frontend.up.railway.app,http://localhost:3000"
cors_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if cors_origins_str == "*":
    origins = ["*"]
    allow_credentials = False  # Wildcards don't work with credentials
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
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["hotelusers"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "identity"}
