from typing import List
from fastapi import APIRouter, UploadFile, Form, File

from src.handlers import (
    register_user_handler,
    verify_user_handler,
    status_user_handler,
    log_user_handler
)
from src.core import logger

router = APIRouter()

@router.post("/register")
async def register_user(
    user_id: str = Form(...),
    file: List[UploadFile] = File(...)
):
    """
    Register a new user with face image data.

    Parameters
    ----------
    user_id : str
        The user ID to register.
    file : List[UploadFile]
        List of uploaded face images (50 required).

    Returns
    -------
    JSON response with registration status and evaluation metrics.
    """
    logger.info(f"Registering user: {user_id}")
    return await register_user_handler(user_id, file)


@router.post("/verify")
async def verify_user(
    user_id: str = Form(...),
    file: UploadFile = Form(...)
):
    """
    Verify a user's identity using a face image.

    Parameters
    ----------
    user_id : str
        The user ID to verify.
    file : UploadFile
        The uploaded face image.

    Returns
    -------
    JSON response with similarity score and match result.
    """
    logger.info(f"Verifying user: {user_id}")
    return await verify_user_handler(user_id, file)

@router.post("/status")
async def status_user(
    user_id: str = Form(...)
):
    """
    Check the registration or verification status of a user.

    Parameters
    ----------
    user_id : str
        The user ID.

    Returns
    -------
    JSON response with the current status of the user.
    """
    logger.info(f"Checking status for user: {user_id}")
    return await status_user_handler(user_id)

@router.post("/log")
async def log_user(
    user_id: str = Form(...),
    durasi: float = Form(...)
):
    """
    Log the verification duration for a user.

    Parameters
    ----------
    user_id : str
        The user ID.
    durasi : float
        The duration of the verification process.

    Returns
    -------
    JSON response indicating log status.
    """
    logger.info(f"Logging duration for user: {user_id}, duration: {durasi}")
    return await log_user_handler(user_id, durasi)