import logging
import traceback

from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings

logger = logging.getLogger(__name__)

class ExceptionMiddleware(BaseHTTPMiddleware):
    """
    Custom middleware to catch unhandled exceptions and return a JSON response.

    In DEBUG mode, the response includes the error message and traceback.
    In PRODUCTION mode, a generic error message is returned to avoid exposing internals.

    Attributes
    ----------
    dispatch : Callable
        The middleware dispatch function that wraps around all incoming requests.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            if settings.DEBUG:
                logger.exception("Unhandled exception during request")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": str(e),
                        "trace": traceback.format_exc().splitlines()
                    }
                )
            else:
                logger.error("Unhandled exception occurred: %s", str(e))
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "message": "Internal Server Error"
                    }
                )
