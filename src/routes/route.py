from fastapi import APIRouter, UploadFile, Form, File
from src.services import service

router = APIRouter()

@router.post("/register")
async def register_user(
    user_id: str = Form(...),
    file: list[UploadFile] = File(...)
):
    return await service.register_user(user_id, file)

@router.post("/verify")
async def verify_user(
    user_id: str = Form(...),
    file: UploadFile = Form(...)
):
    return await service.verify_user(user_id, file)
