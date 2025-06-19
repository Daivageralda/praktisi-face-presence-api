from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.routes import router

app = FastAPI(
    title="API Sistem Presensi Face Recognition Website Praktikum",
    version="1.0.0",
    description="REST API untuk sistem presensi berbasis face recognition menggunakan FaceNet dan cosine similarity.",
)

# Middleware CORS untuk akses lintas domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redirect root ke dokumentasi otomatis
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Register router modular
app.include_router(
    router.router,
    prefix="/presence-api/v1",
    tags=["Face Recognition"]
)
