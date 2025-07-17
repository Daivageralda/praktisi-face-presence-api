import os

from src.core import settings
from src.utils import response
from src.core import logger

async def status_user_handler(user_id: str):
    """
    Check registration status of a user based on the existence of their embedding file.

    This function:
    - Validates the user ID.
    - Checks if the corresponding embedding file exists.
    - Returns a message indicating whether the user has registered.

    Parameters
    ----------
    user_id : str
        The ID of the user whose status is being checked.

    Returns
    -------
    JSONResponse
        A structured response indicating the user's registration status.
    """
    try:
        if not user_id:
            logger.warning("User ID is missing or invalid.")
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
                status_code=200,
                success=True,
                msg="User is not registered.",
                data={"user_id": user_id}
            )

        logger.info(f"User {user_id} is already registered.")
        return response(
            status_code=200,
            success=True,
            msg="User is already registered.",
            data={"user_id": user_id}
        )

    except Exception as e:
        logger.exception(f"Error while checking registration status for user {user_id}: {e}")
        return response(
            status_code=500,
            success=False,
            msg="An error occurred while checking user registration status.",
            data={"error": str(e)}
        )