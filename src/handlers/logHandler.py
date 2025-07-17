from src.core import logger
from src.utils import response, enqueue_duration

async def log_user_handler(user_id: str, durasi: float):
    """
    Handle logging of face verification duration for a user.

    This function:
    - Validates the input user ID and duration.
    - Enqueues the logging operation for background processing.

    Parameters
    ----------
    user_id : str
        The ID of the user.
    durasi : float
        The duration of the verification process in seconds.

    Returns
    -------
    JSONResponse
        A standardized response indicating success or failure.
    """
    try:
        if not user_id:
            logger.warning("Invalid user ID received during logging.")
            return response(
                status_code=400,
                success=False,
                msg="Invalid user ID.",
                data={"received_user_id": user_id}
            )

        if durasi is None or durasi <= 0:
            logger.warning(f"Invalid duration received for user {user_id}: {durasi}")
            return response(
                status_code=400,
                success=False,
                msg="Invalid duration.",
                data={"received_duration": durasi}
            )

        enqueue_duration(user_id=user_id, duration=durasi)
        logger.info(f"Duration {durasi}s successfully enqueued for user {user_id}.")

        return response(
            status_code=200,
            success=True,
            msg="Duration successfully logged.",
            data={"user_id": user_id, "duration": durasi}
        )

    except Exception as e:
        logger.exception(f"Error while logging duration for user {user_id}: {e}")
        return response(
            status_code=500,
            success=False,
            msg="An internal error occurred during duration logging.",
            data={"error": str(e)}
        )
