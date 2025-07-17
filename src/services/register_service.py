import asyncio

from fastapi import UploadFile
from typing import List,Dict, Any

from src.core import executor, logger
from src.utils import (
    train_test_split_and_save,response,
    process_images_batch,
    validate_embeddings,
    save_embedding)
from src.services import evaluate_user

async def register_user(user_id: str, file: List[UploadFile]) -> Dict[str, Any]:
    """
    Register a new user by processing uploaded face images.

    This function:
    - Reads and decodes uploaded images in async batches.
    - Splits data into training and testing images.
    - Extracts face embeddings from training images.
    - Validates the extracted embeddings.
    - Saves the embedding to disk.
    - Evaluates the registration quality.

    Parameters
    ----------
    user_id : str
        The ID of the user to register.

    file : List[UploadFile]
        List of image files uploaded by the user (expected: 50 images).

    Returns
    -------
    dict
        A standardized API response indicating success or failure.
    """
    try:
        images_bytes = []

        async def read_file(frame):
            try:
                return await frame.read()
            except Exception as e:
                logger.error(f"Error reading file: {e}")
                return None

        batch_size = 10
        for i in range(0, len(file), batch_size):
            batch = file[i:i + batch_size]
            batch_contents = await asyncio.gather(*[read_file(frame) for frame in batch])
            valid_contents = [content for content in batch_contents if content]
            images_bytes.extend(valid_contents)

        if len(images_bytes) != 50:
            logger.warning(f"User {user_id} uploaded {len(images_bytes)} images (expected 50).")
            return response(
                status_code=400,
                success=False,
                msg="Jumlah gambar tidak valid",
                data={"Jumlah gambar diterima": len(images_bytes)}
            )

        try:
            loop = asyncio.get_event_loop()
            train_images = await loop.run_in_executor(
                executor, train_test_split_and_save, images_bytes, user_id
            )

            if not train_images:
                logger.warning(f"Failed to split and save test images for user {user_id}")
                return response(
                    status_code=400,
                    success=False,
                    msg="Gagal menyimpan gambar hasil split",
                    data={}
                )
        except Exception as e:
            logger.exception(f"Error during train/test split for user {user_id}")
            return response(
                status_code=500,
                success=False,
                msg="Terjadi kesalahan saat proses split data",
                data={"error": str(e)}
            )

        try:
            embeddings = await process_images_batch(train_images, batch_size=5)

            if not embeddings:
                logger.error(f"No valid embeddings extracted for user {user_id}")
                return response(
                    status_code=500,
                    success=False,
                    msg="Gagal mengekstrak embedding dari gambar",
                    data={}
                )

            if not validate_embeddings(embeddings):
                logger.warning(f"Invalid embeddings after extraction for user {user_id}")
                return response(
                    status_code=500,
                    success=False,
                    msg="Embedding tidak valid setelah ekstraksi",
                    data={}
                )

        except Exception as e:
            logger.exception(f"Error extracting embeddings for user {user_id}")
            return response(
                status_code=500,
                success=False,
                msg="Terjadi kesalahan saat proses ekstrak embedding",
                data={"error": str(e)}
            )

        try:
            if save_embedding(embeddings, user_id):
                logger.info(f"Embeddings saved successfully for user {user_id}, starting evaluation.")
                return await evaluate_user(user_id)
            else:
                logger.error(f"Failed to save embedding for user {user_id}")
                return response(
                    status_code=500,
                    success=False,
                    msg="Gagal menyimpan embedding",
                    data={}
                )
        except Exception as e:
            logger.exception(f"Error saving embedding or evaluating user {user_id}")
            return response(
                status_code=500,
                success=False,
                msg="Terjadi kesalahan saat simpan dan evaluasi",
                data={"error": str(e)}
            )

    except Exception as e:
        logger.exception(f"Unhandled error during registration for user {user_id}")
        return response(
            status_code=500,
            success=False,
            msg="Terjadi kesalahan dalam proses registrasi",
            data={"error": str(e)}
        )