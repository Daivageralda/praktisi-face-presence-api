from fastapi import UploadFile
from typing import List, Any, Dict

from src.utils import response
from src.core import settings, logger
from src.services import register_user

async def register_user_handler(user_id: str, files: List[UploadFile]) -> Dict[str, Any]:
    """
    Handle user face registration via uploaded images.

    This function:
    - Validates the number of uploaded images.
    - Validates the provided user ID.
    - Calls the registration service.
    - Returns a standardized response based on the result.

    Parameters
    ----------
    user_id : str
        The ID of the user to register.
    files : List[UploadFile]
        A list of uploaded image files for registration.

    Returns
    -------
    JSONResponse
        A response indicating the result of the registration process.
    """
    try:
        if not user_id:
            logger.warning("Invalid user ID provided during registration.")
            return response(
                status_code=400,
                success=False,
                msg="Invalid user ID.",
                data={"received_user_id": user_id}
            )

        if len(files) != settings.IMAGE_COUNT:
            logger.warning(f"Incorrect number of images for user {user_id}: received {len(files)}")
            return response(
                status_code=400,
                success=False,
                msg="Incorrect number of images.",
                data={"received_image_count": len(files)}
            )

        result = await register_user(user_id, files)
        print(result)
        if isinstance(result, dict) and not result["success"]:
            logger.error(f"Registration failed for user {user_id}: {result}")
            return result

        logger.info(f"Face registration successful for user {user_id}.")
        return response(
            status_code=200,
            success=True,
            msg="Face registration successful.",
            data=result.get("data")
        )

    except Exception as e:
        logger.exception(f"Unexpected error during registration for user {user_id}: {e}")
        return response(
            status_code=500,
            success=False,
            msg="An internal error occurred during face registration.",
            data={"error": str(e)}
        )