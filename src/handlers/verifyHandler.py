import os

from fastapi import UploadFile

from src.core import logger
from src.core import settings
from src.utils import response
from src.services import verify_user


async def verify_user_handler(user_id: str, file: UploadFile):
    """
    Handle face verification request from user.

    This function:
    - Validates the input user ID and uploaded file.
    - Checks whether the user has already registered.
    - Invokes the face verification service and returns the result.

    Parameters
    ----------
    user_id : str
        The ID of the user to verify.
    file : UploadFile
        The image file uploaded for verification.

    Returns
    -------
    JSONResponse
        Response indicating the result of face verification.
    """
    try:
        if file is None:
            logger.warning("No file uploaded for verification.")
            return response(
                status_code=400,
                success=False,
                msg="No image uploaded for verification.",
                data={"file": None}
            )

        if not user_id:
            logger.warning("User ID not provided.")
            return response(
                status_code=400,
                success=False,
                msg="Invalid user ID.",
                data={"received_user_id": user_id}
            )

        embedding_path = os.path.join(settings.EMBEDDING_DIR, f"{user_id}.pkl")
        if not os.path.exists(embedding_path):
            logger.info(f"User {user_id} has not registered.")
            return response(
                status_code=400,
                success=False,
                msg="User is not registered.",
                data={"user_id": user_id}
            )

        result = await verify_user(user_id, file)

        if isinstance(result, dict) and not result["success"]:
            logger.warning(f"Verification failed for user {user_id}: {result}")
            return result

        logger.info(f"Verification successful for user {user_id}")
        return response(
            status_code=200,
            success=True,
            msg="Face verification successful.",
            data=result.get("data")
        )

    except Exception as e:
        logger.exception(f"Error during face verification for user {user_id}: {e}")
        return response(
            status_code=500,
            success=False,
            msg="An error occurred during face verification.",
            data={"error": str(e)}
        )
