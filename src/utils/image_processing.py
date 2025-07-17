import asyncio
import numpy as np

from typing import List, Optional

from src.core import settings, executor, logger
from src.utils import load_image_from_bytes, extract_embedding

def process_single_image(content: bytes) -> Optional[np.ndarray]:
    """
    Process a single image to extract its face embedding.

    This function performs the following steps:
    1. Loads and decodes image bytes into an RGB image.
    2. Resizes the image to the required input size.
    3. Extracts the face embedding using the face embedding model.
    4. Validates the resulting embedding (non-empty, numeric, no NaNs or Infs).

    Parameters
    ----------
    content : bytes
        Raw image bytes.

    Returns
    -------
    np.ndarray or None
        A valid embedding vector of shape (1, N) if successful,
        or None if the image is invalid or embedding fails.
    """
    try:
        if not content:
            logger.warning("Image content is empty")
            return None

        image = load_image_from_bytes(content)
        image = image.resize((settings.IMAGE_SIZE, settings.IMAGE_SIZE))

        emb = extract_embedding(image_bytes=content)

        if emb is None or emb.size == 0:
            logger.warning("Embedding is None or empty")
            return None

        if np.any(np.isnan(emb)) or np.any(np.isinf(emb)):
            logger.warning("Embedding contains NaN or Inf values")
            return None

        return emb

    except Exception as e:
        logger.error(f"Error while processing single image: {e}")
        return None

async def process_images_batch(images_bytes: List[bytes], batch_size: int = 5) -> List[np.ndarray]:
    """
    Process a list of image bytes in batches and extract their face embeddings.

    This function uses an executor to process images asynchronously in small batches
    to prevent memory overflow. It filters out invalid embeddings before returning.

    Parameters
    ----------
    images_bytes : List[bytes]
        List of raw image bytes.
    batch_size : int, optional
        Number of images to process in one batch (default is 5).

    Returns
    -------
    List[np.ndarray]
        A list of valid face embedding vectors (ndarrays).
    """
    embeddings = []

    for i in range(0, len(images_bytes), batch_size):
        batch = images_bytes[i:i + batch_size]
        current_batch = i // batch_size + 1
        total_batches = (len(images_bytes) + batch_size - 1) // batch_size
        logger.info(f"Processing batch {current_batch}/{total_batches}")

        loop = asyncio.get_event_loop()
        batch_tasks = [
            loop.run_in_executor(executor, process_single_image, content)
            for content in batch
        ]

        try:
            batch_embeddings = await asyncio.gather(*batch_tasks)
        except asyncio.TimeoutError:
            logger.error(f"Timeout while processing batch {current_batch}/{total_batches}")
            batch_embeddings = []

        valid_embeddings = [emb for emb in batch_embeddings if emb is not None]
        embeddings.extend(valid_embeddings)

        await asyncio.sleep(0.1)

    logger.info(f"Finished processing {len(embeddings)} valid embeddings from {len(images_bytes)} images")
    return embeddings