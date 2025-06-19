import os
import shutil
from io import BytesIO
from PIL import Image
import pytest

from src.utils.helper import (
    load_image_from_bytes,
    train_test_split_and_save,
    response,
)

# Helper untuk membuat dummy image bytes
def create_dummy_image_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color="blue")
    buf = BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()

@pytest.fixture
def dummy_images():
    return [create_dummy_image_bytes() for _ in range(10)]

@pytest.fixture
def test_user_id():
    return "test_user_123"

def test_load_image_from_bytes():
    dummy_bytes = create_dummy_image_bytes()
    image = load_image_from_bytes(dummy_bytes)

    assert isinstance(image, Image.Image)
    assert image.mode == "RGB"
    assert image.size == (100, 100)

def test_train_test_split_and_save(dummy_images, test_user_id):
    # Jalankan fungsi
    train_images = train_test_split_and_save(dummy_images, test_user_id, test_ratio=0.2)

    # Direktori test
    test_dir = os.path.join("src", "storage", "test_images", test_user_id)
    saved_files = os.listdir(test_dir)

    # Asersi
    assert len(train_images) == 8  # 80% dari 10 gambar
    assert len(saved_files) == 2   # 20% disimpan
    assert all(fname.endswith(".webp") for fname in saved_files)

    # Cleanup setelah test
    # shutil.rmtree(os.path.join("src", "storage", "test_images", test_user_id))

def test_response_format():
    resp = response(200, True, "Berhasil", {"key": "value"})

    assert isinstance(resp, dict)
    assert resp["status_code"] == 200
    assert resp["success"] is True
    assert resp["msg"] == "Berhasil"
    assert resp["data"] == {"key": "value"}
