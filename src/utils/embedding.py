import os
import joblib
import threading
import numpy as np

from tensorflow.lite.python.interpreter import Interpreter
from PIL import Image
from io import BytesIO
from typing import List
from threading import local

from src.models import load_model
from src.core import logger, settings

def validate_embeddings(embeddings: List[np.ndarray]) -> bool:
    """
    Validate a list of face embeddings.

    This function checks whether each embedding in the list:
    - Is a NumPy array.
    - Is not None.
    - Has non-zero size.
    - Does not contain NaN or Inf values.

    Parameters
    ----------
    embeddings : List[np.ndarray]
        A list of face embeddings to validate.

    Returns
    -------
    bool
        True if all embeddings are valid, False otherwise.
    """
    try:
        if not embeddings:
            logger.warning("Validasi gagal: embeddings kosong")
            return False

        for i, emb in enumerate(embeddings):
            if (
                emb is None or
                not isinstance(emb, np.ndarray) or
                emb.size == 0 or
                np.any(np.isnan(emb)) or
                np.any(np.isinf(emb))
            ):
                logger.warning(f"Validasi gagal: embedding indeks {i} tidak valid")
                return False

        logger.info(f"Validasi berhasil: {len(embeddings)} embeddings valid")
        return True

    except Exception as e:
        logger.exception(f"Terjadi kesalahan saat validasi embeddings: {e}")
        return False


def save_embedding(embedding, user_id) -> bool:
    """
    Save a validated face embedding to disk for a specific user.

    This function:
    - Validates the input embedding (must be a non-empty list or ndarray).
    - Converts list embeddings to ndarray if necessary.
    - Ensures 2D shape for single embeddings.
    - Saves the embedding to a `.pkl` file in the configured directory.

    Parameters
    ----------
    embedding : list or np.ndarray
        The face embedding(s) to save. Can be a single or multiple embeddings.
    user_id : str
        The ID of the user, used to name the saved embedding file.

    Returns
    -------
    bool
        True if the embedding was successfully saved, False otherwise.
    """
    try:
        if embedding is None or not isinstance(embedding, (list, np.ndarray)) or len(embedding) == 0:
            logger.warning(f"Embedding untuk user {user_id} tidak valid (kosong atau bukan list/ndarray)")
            return False

        if isinstance(embedding, list):
            from src.services.register_service import validate_embeddings  # hindari circular import
            if not validate_embeddings(embedding):
                logger.warning(f"Embedding list tidak lolos validasi untuk user {user_id}")
                return False
            embedding = np.array(embedding)

        elif isinstance(embedding, np.ndarray):
            if embedding.size == 0:
                logger.warning(f"Embedding array kosong untuk user {user_id}")
                return False

            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)

        else:
            logger.error(f"Tipe embedding tidak didukung: {type(embedding)} untuk user {user_id}")
            return False

        os.makedirs(settings.EMBEDDING_DIR, exist_ok=True)
        path_model = os.path.join(settings.EMBEDDING_DIR, f"{user_id}.pkl")
        joblib.dump(embedding, path_model)
        logger.info(f"Embedding berhasil disimpan untuk user {user_id} di {path_model}")
        return True

    except Exception as e:
        logger.exception(f"Gagal menyimpan embedding untuk user {user_id}: {e}")
        return False
    
# Load model once at module import
# interpreter, input_index, output_index = load_model()
# _model_lock = threading.Lock()
_thread_local = local()
def get_thread_interpreter():
    """
    Buat TFLite interpreter khusus untuk thread saat ini (bukan global).
    """
    if not hasattr(_thread_local, "interpreter"):
        interpreter = Interpreter(
            model_path=str(settings.MODEL_PATH),
            num_threads=settings.TF_NUM_THREADS
        )
        interpreter.allocate_tensors()
        _thread_local.interpreter = interpreter
        _thread_local.input_index = interpreter.get_input_details()[0]["index"]
        _thread_local.output_index = interpreter.get_output_details()[0]["index"]
    
    return _thread_local.interpreter, _thread_local.input_index, _thread_local.output_index

def extract_embedding(image_bytes: bytes) -> np.ndarray:
    """
    Extract a face embedding from image bytes using a preloaded TFLite model.

    This function performs:
    - Image validation and preprocessing.
    - Inference using a TensorFlow Lite interpreter.
    - Validation of output embedding.

    Parameters
    ----------
    image_bytes : bytes
        Raw image bytes in any format supported by PIL.

    Returns
    -------
    np.ndarray
        1D embedding vector of shape (EMBEDDING_DIM,), or a zero vector if extraction fails.
    """
    try:
        if not image_bytes:
            raise ValueError("Empty image bytes provided")

        image = Image.open(BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')

        image = image.resize(
            (settings.IMAGE_SIZE, settings.IMAGE_SIZE),
            Image.Resampling.LANCZOS
        )
        img_array = np.asarray(image, dtype=np.float32) / 255.0

        if img_array.shape != (settings.IMAGE_SIZE, settings.IMAGE_SIZE, settings.IMAGE_CHANNEL):
            raise ValueError(f"Invalid image shape: {img_array.shape}")

        img_array = np.expand_dims(img_array, axis=0)

        # Gunakan interpreter khusus thread ini
        interpreter, input_index, output_index = get_thread_interpreter()

        interpreter.set_tensor(input_index, img_array)
        interpreter.invoke()

       # langsung copy + slice di sini
        raw_output = interpreter.get_tensor(output_index)
        embedding_1d = np.array(raw_output[0] if len(raw_output.shape) > 1 else raw_output, copy=True)

        image.close()

        if embedding_1d is None or embedding_1d.size == 0:
            raise ValueError("Empty embedding returned from model")

        if np.any(np.isnan(embedding_1d)):
            raise ValueError("Embedding contains NaN values")

        if np.any(np.isinf(embedding_1d)):
            raise ValueError("Embedding contains infinite values")

        return embedding_1d

    except Exception as e:
        logger.exception("Failed to extract embedding: %s", e)
        return np.zeros(settings.EMBEDDING_DIM, dtype=np.float32)