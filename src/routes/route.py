from fastapi import APIRouter, UploadFile, Form, File
from src.handlers import (
    register_user_handler,
    verify_user_handler
)

router = APIRouter()

@router.post("/register")
async def register_user(
    user_id: str = Form(...),
    file: list[UploadFile] = File(...)
):
    return await register_user_handler(user_id, file)

@router.post("/verify")
async def verify_user(
    user_id: str = Form(...),
    file: UploadFile = Form(...)
):
    return await verify_user_handler(user_id, file)
