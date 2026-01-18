from sqlmodel import create_engine, Session
from dotenv import load_dotenv
import os
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Fix for Railway/Heroku: SQLAlchemy requires 'postgresql://', but some providers give 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Only enable SQL echo if DEBUG is explicitly true
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

engine = create_engine(
    DATABASE_URL,
    echo=DEBUG_MODE,    # Controlled by env var
    pool_pre_ping=True  # avoids stale connections
)



