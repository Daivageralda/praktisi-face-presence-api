from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.routes import route
from src.middleware import ExceptionMiddleware
from src.utils import start_spreadsheet, get_thread_interpreter
from src.core import cleanup_executor, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context for startup and shutdown routines.

    This function initializes external services such as the spreadsheet logger
    and handles resource cleanup upon shutdown.
    """
    try:
        get_thread_interpreter()
        logger.info("TFLite interpreter initialized on startup.")

        start_spreadsheet()
        logger.info("[BatchLogger] Spreadsheet integration activated successfully.")
    except Exception as e:
        logger.exception(f"[BatchLogger] Failed to activate spreadsheet logging: {e}")

    yield

    logger.info("[App] Shutting down application...")
    cleanup_executor()
    logger.info("[App] Executor resources cleaned up.")


app = FastAPI(
    title="Face Recognition Presence System API - Information Systems Practicum",
    version="1.0.0",
    description=(
        "RESTful API for a facial recognition-based attendance system, "
        "utilizing FaceNet embeddings and cosine similarity."
    ),
    lifespan=lifespan
)

# Register global middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://praktisi-lab.my.id.com",
        "https://www.praktisi-lab.my.id.com"  # Jangan lupa www juga
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ExceptionMiddleware)

@app.get("/", include_in_schema=False)
async def root():
    """
    Redirects root URL to the Swagger documentation UI.
    """
    logger.info("[Root] Redirecting to /docs")
    return RedirectResponse(url="/docs")


# Register all application routes
app.include_router(
    route.router,
    prefix="/presence-api/v1",
    tags=["Face Recognition"]
)

logger.info("[FastAPI] Application initialized and ready.")
