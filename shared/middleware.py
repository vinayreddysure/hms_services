import sys
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import traceback

# Setup basic logging config
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_logger")

class LogExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Log the full error with traceback
            logger.error(f"Global Exception on {request.method} {request.url}")
            logger.error(traceback.format_exc())
            
            # Return a generic 500 error to user
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error. Please check server logs for details."}
            )
