from fastapi import APIRouter, UploadFile, Form, File
from src.services import service

router = APIRouter()

@router.post(
    "/register",
    summary="Registrasi Wajah",
    description="Menerima 10 gambar wajah pengguna, menyimpan embedding, dan melakukan evaluasi dengan confusion matrix."
)
async def register_user(
    user_id: str = Form(...),
    file: list[UploadFile] = File(...)
):
    return await service.register_user(user_id, file)


@router.post(
    "/verify",
    summary="Verifikasi Wajah",
    description="Verifikasi wajah berdasarkan gambar yang diunggah dan pembandingan dengan embedding yang telah tersimpan."
)
async def verify_user(
    user_id: str = Form(...),
    file: UploadFile = Form(...)
):
    return await service.verify_user(user_id, file)
