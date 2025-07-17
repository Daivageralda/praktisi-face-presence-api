import os
import joblib
import asyncio
import numpy as np

from fastapi import UploadFile
from typing import Dict, Any
from sklearn.metrics.pairwise import cosine_similarity

from src.core import settings, executor, logger
from src.utils import response, enqueue_verification, extract_embedding


def _compare_embedding_sync(user_id: str, image_bytes: bytes) -> dict:
    """
    Compare an input image embedding with a user's stored embeddings.

    This synchronous function:
    - Loads the stored embeddings for the specified user.
    - Extracts the embedding from the provided image bytes.
    - Computes cosine similarity between the input and stored embeddings.
    - Returns the similarity score or a structured error response.

    Parameters
    ----------
    user_id : str
        The ID of the user whose embeddings will be used for comparison.
    image_bytes : bytes
        Raw bytes of the input image to be compared.

    Returns
    -------
    dict
        A dictionary containing:
        - "error": True if an error occurred, False otherwise.
        - "similarity": The similarity score if successful.
        - "data": A FastAPI-style response object if an error occurred.
    """
    try:
        model_path = os.path.join(settings.EMBEDDING_DIR, f"{user_id}.pkl")
        if not os.path.exists(model_path):
            logger.warning(f"Embedding file not found for user {user_id}")
            return {
                "error": True,
                "data": response(
                    status_code=404,
                    success=False,
                    msg=f"User {user_id} not found.",
                    data={}
                )
            }

        embeddings = joblib.load(model_path)
        input_embedding = extract_embedding(image_bytes)

        if input_embedding is None or input_embedding.size == 0:
            logger.warning(f"Invalid embedding extracted for user {user_id}")
            raise ValueError("Invalid embedding")

        similarities = cosine_similarity([input_embedding], embeddings)
        similarity = float(np.mean(similarities))
        logger.info(f"Computed similarity for user {user_id}: {similarity:.4f}")

        return {"error": False, "similarity": similarity}

    except Exception as e:
        logger.exception(f"Error comparing embedding for user {user_id}")
        return {
            "error": True,
            "data": response(
                status_code=500,
                success=False,
                msg="Internal error occurred while computing cosine similarity",
                data={"error": str(e)}
            )
        }



async def compare_embedding(user_id: str, image_bytes: bytes) -> dict:
    """
    Asynchronously compare a user's input face embedding with stored embeddings.

    This function offloads the synchronous comparison task to a thread pool executor
    to avoid blocking the event loop. It returns the similarity result or an error response.

    Parameters
    ----------
    user_id : str
        The ID of the user whose embedding will be compared.
    image_bytes : bytes
        Raw bytes of the uploaded face image.

    Returns
    -------
    dict
        A dictionary containing the comparison result or error response.
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, _compare_embedding_sync, user_id, image_bytes)
        logger.info(f"Comparison completed for user {user_id} with result: {result}")
        return result
    except Exception as e:
        logger.exception(f"Failed to compare embedding for user {user_id}: {e}")
        return {
            "error": True,
            "data": {
                "status_code": 500,
                "success": False,
                "msg": "Internal error during embedding comparison",
                "data": {"error": str(e)}
            }
        }


async def verify_user(user_id: str, file: UploadFile) -> Dict[str, Any]:
    """
    Verify a user's identity by comparing the uploaded face image with stored embeddings.

    This function:
    - Reads the uploaded image file.
    - Extracts and compares its embedding to the stored embeddings.
    - Determines if the user matches based on a similarity threshold.
    - Logs the verification result asynchronously.

    Parameters
    ----------
    user_id : str
        The ID of the user to verify.
    file : UploadFile
        The uploaded face image.

    Returns
    -------
    Any
        A response dictionary containing verification result and similarity score.
    """
    logger.info(f"Starting verification for user: {user_id}")
    
    try:
        image_bytes = await file.read()
        result = await compare_embedding(user_id, image_bytes)

        if result["error"]:
            logger.warning(f"Verification failed for user {user_id}: {result['data']}")
            return result["data"]

        similarity_score = result["similarity"]
        result_label = "Match" if similarity_score > settings.THRESHOLD else "Not Match"

        enqueue_verification(user_id, result_label)

        logger.info(f"Verification success for user {user_id}: {result_label} (score={similarity_score:.5f})")

        return response(
            status_code=200,
            success=True,
            msg="Verification successful",
            data={
                "similarity": round(similarity_score, 5),
                "result": result_label
            }
        )

    except Exception as e:
        logger.exception(f"Internal error during verification for user {user_id}")
        return response(
            status_code=500,
            success=False,
            msg="Internal error during user verification",
            data={"error": str(e)}
        )