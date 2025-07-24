import os
import random
import joblib
import asyncio
import numpy as np

from glob import glob
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import confusion_matrix, classification_report

from src.core import settings, executor, logger
from src.utils import load_image_from_bytes, response, enqueue_registration, extract_embedding

def evaluate_single_image(path: str, saved_embeddings: np.ndarray) -> int:
    """
    Evaluate a single test image against saved face embeddings.

    This function:
    - Loads the image from the given path.
    - Extracts the face embedding from the image.
    - Calculates cosine similarity against all saved user embeddings.
    - Returns 1 (Real) if the maximum similarity exceeds the threshold, otherwise 0 (Fake).

    Parameters
    ----------
    path : str
        Path to the image file to evaluate.
    saved_embeddings : np.ndarray
        A 2D array containing the user's saved face embeddings.

    Returns
    -------
    int
        Predicted label: 1 if matched (Real), 0 if not matched (Fake).
    """
    try:
        with open(path, "rb") as f:
            image_bytes = f.read()

        image = load_image_from_bytes(image_bytes)
        image = image.resize((settings.IMAGE_SIZE, settings.IMAGE_SIZE))
        emb = extract_embedding(image_bytes)

        if emb is None or emb.size == 0:
            logger.warning(f"Embedding gagal diekstrak dari gambar: {path}")
            return 0

        if np.any(np.isnan(emb)) or np.any(np.isinf(emb)):
            logger.warning(f"Embedding tidak valid (NaN/Inf) dari gambar: {path}")
            return 0

        similarities = cosine_similarity([emb], saved_embeddings)[0]
        max_similarity = np.max(similarities)

        return 1 if max_similarity > settings.THRESHOLD else 0

    except Exception as e:
        logger.exception(f"Gagal mengevaluasi gambar {path}: {e}")
        return 0

async def evaluate_user(user_id: str):
    """
    Evaluate the face recognition performance of a user using saved embeddings.

    This function:
    - Retrieves the user's test images and random images from other users.
    - Evaluates these images against the user's saved face embeddings.
    - Generates a confusion matrix and a classification report.
    - Logs the evaluation results to an external system (e.g., Google Sheets).

    Parameters
    ----------
    user_id : str
        The ID of the user to evaluate.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the evaluation results, including the confusion matrix and classification report.
    """
    try:
        logger.info(f"Evaluating ...")        
        user_test_dir = os.path.join(settings.IMAGE_DIR, user_id)
        if not os.path.exists(user_test_dir):
            return response(404, False, f"Folder test_image user {user_id} tidak ditemukan.", {})

        user_test_paths = sorted(glob(os.path.join(user_test_dir, "*.webp")))
        if not user_test_paths:
            return response(404, False, "Tidak ada gambar test user ditemukan.", {})

        other_images = glob(os.path.join(settings.DATASET_DIR, "*.webp"))

        if len(other_images) < len(user_test_paths):
            return response(
                400, False, "Tidak cukup gambar random dari user lain untuk evaluasi.",
                {"jumlah_tersedia": len(other_images)}
            )

        random_sample_paths = random.sample(other_images, len(user_test_paths))
        combined_paths = user_test_paths + random_sample_paths
        true_labels = [1] * len(user_test_paths) + [0] * len(random_sample_paths)

        embed_path = os.path.join(settings.EMBEDDING_DIR, f"{user_id}.pkl")
        if not os.path.exists(embed_path):
            return response(404, False, "Embedding pengguna tidak ditemukan.", {})

        saved_embeddings = joblib.load(embed_path)

        predicted_labels = []
        batch_size = 5
        loop = asyncio.get_event_loop()

        for i in range(0, len(combined_paths), batch_size):
            batch_paths = combined_paths[i:i + batch_size]
            logger.info(f"Evaluating batch {i // batch_size + 1}/{(len(combined_paths) + batch_size - 1) // batch_size}")

            batch_tasks = [
                loop.run_in_executor(executor, evaluate_single_image, path, saved_embeddings)
                for path in batch_paths
            ]

            try:
                batch_predictions = await asyncio.gather(*batch_tasks)
                predicted_labels.extend(batch_predictions)
            except asyncio.TimeoutError:
                logger.warning("Timeout saat evaluasi batch predictions")

            # await asyncio.sleep(0.1)

        predicted_labels = [max(0, min(1, int(pred))) for pred in predicted_labels]

        if len(set(true_labels)) < 2:
            logger.warning("Hanya satu kelas pada true labels")
        if len(set(predicted_labels)) < 2:
            logger.warning("Hanya satu kelas pada predicted labels")

        try:
            cm = confusion_matrix(true_labels, predicted_labels).tolist()
            report = classification_report(
                true_labels, predicted_labels,
                target_names=["Fake", "Real"],
                output_dict=True,
                zero_division=0
            )
        except Exception as e:
            logger.exception(f"Error generating metrics: {e}")
            cm = [[0, 0], [0, 0]]
            report = {
                "Fake": {"precision": 0.0, "recall": 0.0, "f1-score": 0.0, "support": 0},
                "Real": {"precision": 0.0, "recall": 0.0, "f1-score": 0.0, "support": 0},
                "accuracy": 0.0,
                "macro avg": {"precision": 0.0, "recall": 0.0, "f1-score": 0.0, "support": 0},
                "weighted avg": {"precision": 0.0, "recall": 0.0, "f1-score": 0.0, "support": 0}
            }

        loop.run_in_executor(executor, enqueue_registration, user_id, cm)

        return response(
            status_code=200,
            success=True,
            msg="Evaluasi user berhasil dilakukan",
            data={
                "confusion_matrix": cm,
                "classification_report": report
            }
        )

    except Exception as e:
        logger.exception(f"Terjadi kesalahan saat evaluasi user {user_id}: {e}")
        return response(
            status_code=500,
            success=False,
            msg="Terjadi kesalahan internal saat evaluasi user",
            data={"error": str(e)}
        )