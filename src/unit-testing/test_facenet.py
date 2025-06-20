import pytest
import numpy as np
from PIL import Image
from io import BytesIO

from src.models.facenet import extract_embedding, load_model

@pytest.fixture(scope="module")
def dummy_image_bytes():
    """
    Fixture untuk menghasilkan gambar RGB dummy berukuran 160x160 dan mengubahnya menjadi bytes.
    """
    dummy_image = Image.new("RGB", (160, 160), color=(255, 255, 255))
    byte_arr = BytesIO()
    dummy_image.save(byte_arr, format='JPEG')
    return byte_arr.getvalue()

def test_extract_embedding_output_shape(dummy_image_bytes):
    """
    Memastikan bahwa output embedding memiliki bentuk dan tipe data yang benar.
    """
    embedding = extract_embedding(dummy_image_bytes)
    assert isinstance(embedding, np.ndarray), "Hasil harus berupa NumPy array"
    assert embedding.ndim == 1, "Embedding harus berbentuk vektor 1 dimensi"
    assert embedding.shape[0] in [128, 512], "Panjang embedding harus 128 atau 512"

def test_embedding_model_loaded_once():
    """
    Memastikan bahwa model hanya dimuat sekali (singleton behavior).
    """
    interpreter1, input_idx1, output_idx1 = load_model()
    interpreter2, input_idx2, output_idx2 = load_model()
    assert interpreter1 is interpreter2, "Interpreter harus singleton (sama)"
    assert input_idx1 == input_idx2
    assert output_idx1 == output_idx2
