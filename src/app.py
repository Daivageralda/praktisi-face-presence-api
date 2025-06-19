from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.routes import route

apps = FastAPI(
    title="API Sistem Presensi Face Recognition Website Praktikum",
    version="1.0.0",
    description="REST API untuk sistem presensi berbasis face recognition menggunakan FaceNet dan cosine similarity.",
)

apps.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@apps.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# PENTING: Pastikan ini tidak salah!
apps.include_router(
    route.router,
    prefix="/presence-api/v1",
    tags=["Face Recognition"]
)
