import uvicorn
from src.core import settings, logger


def start_server():
    """
    Start the FastAPI server using Uvicorn with specified settings.

    This function initializes the application with optional auto-reload for development,
    configurable logging level, and custom worker count.
    """
    try:
        uvicorn.run(
            "src.app:app",
            host="0.0.0.0",
            port=settings.API_PORT,
            reload=settings.DEBUG,
            reload_excludes=["src/logs"],
            log_level="debug" if settings.DEBUG else "info",
            workers=settings.API_WORKERS
        )
    except Exception as e:
        logger.exception(f"[Startup] Failed to launch server: {e}")


if __name__ == "__main__":
    start_server()
