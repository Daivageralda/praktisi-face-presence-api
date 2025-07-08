from fastapi import APIRouter, UploadFile, Form, File
from src.handlers import (
    register_user_handler,
    verify_user_handler,
    status_user_handler,
    log_user_handler
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

@router.post("/log")
async def log_user(
    user_id: str = Form(...),
    durasi: float = Form(...)
):
    print(user_id)
    print(durasi)
    return await log_user_handler(user_id, durasi)

@router.post("/status")
async def status_user(
    user_id: str = Form(...)
):
    return await status_user_handler(user_id)