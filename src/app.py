import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from src.utils import initialize_sheets_connection, periodic_refresh
from src.routes import route


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await initialize_sheets_connection()
    except Exception as e:
        print(f"Warm-up failed: {e}")
    
    asyncio.create_task(periodic_refresh())
    yield

app = FastAPI(
    title="API Sistem Presensi Face Recognition Website Praktikum",
    version="1.0.0",
    description="REST API untuk sistem presensi berbasis face recognition menggunakan FaceNet dan cosine similarity.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# PENTING: Pastikan ini tidak salah!
app.include_router(
    route.router,
    prefix="/presence-api/v1",
    tags=["Face Recognition"]
)
