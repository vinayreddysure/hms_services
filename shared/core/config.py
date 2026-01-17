import os

# usage: openssl rand -hex 32
# usage: openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Fallback ONLY for really basic local dev if needed, but best to enforce env var
    # raising error to enforce production safety
    raise ValueError("SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
