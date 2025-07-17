import pytest
import asyncio
from io import BytesIO
from PIL import Image

from fastapi import UploadFile
from starlette.datastructures import UploadFile

from src.handlers import register_user_handler, verify_user_handler, status_user_handler


# === Utility ===
def create_dummy_image_bytes(color=(255, 0, 0)):
    img = Image.new("RGB", (160, 160), color=color)
    buffer = BytesIO()
    img.save(buffer, format="WEBP")
    return buffer.getvalue()


def create_upload_file(name: str, content: bytes):
    file = BytesIO(content)
    return UploadFile(filename=name, file=file)



# # === Fixture untuk bersih-bersih ===
# @pytest.fixture(scope="function", autouse=True)
# def cleanup_storage():
#     yield
#     shutil.rmtree("src/storage/embeddings", ignore_errors=True)
#     shutil.rmtree("src/storage/test_images", ignore_errors=True)


# === Test Register ===
@pytest.mark.asyncio
async def test_register_user_success():
    user_id = "testuser"
    dummy_images = [create_upload_file(f"img_{i}.webp", create_dummy_image_bytes()) for i in range(50)]

    response = await register_user_handler(user_id, dummy_images)

    assert response["status_code"] == 200
    assert response["success"] is True
    assert "Registrasi Wajah Berhasil" in response["msg"]
    assert "confusion_matrix" in response["data"]
    assert "classification_report" in response["data"]


@pytest.mark.asyncio
async def test_register_user_fail_if_less_than_10_images():
    user_id = "testuser"
    dummy_images = [create_upload_file(f"img_{i}.webp", create_dummy_image_bytes()) for i in range(5)]

    response = await register_user_handler(user_id, dummy_images)

    assert response["status_code"] == 400
    assert response["success"] is False
    assert response["msg"] == "Kesalahan Jumlah Gambar"
    assert response["data"] == {"Gambar diterima": len(dummy_images)}


# === Test Verify ===
@pytest.mark.asyncio
async def test_verify_user_success():
    user_id = "testuser"
    dummy_images = [create_upload_file(f"img_{i}.webp", create_dummy_image_bytes()) for i in range(10)]
    await register_user_handler(user_id, dummy_images)

    verify_file = create_upload_file("verify.webp", create_dummy_image_bytes())
    response = await verify_user_handler(user_id, verify_file)

    assert response["status_code"] == 200
    assert response["success"] is True
    assert "similarity" in response["data"]
    assert response["data"]["result"] in ["Match", "Not Match"]


@pytest.mark.asyncio
async def test_verify_user_fail_if_user_not_registered():
    user_id = "nonexistent_user"
    verify_file = create_upload_file("verify.webp", create_dummy_image_bytes())

    response = await verify_user_handler(user_id, verify_file)

    assert response["status_code"] == 400
    assert response["success"] is False
    assert response["msg"] == f"Pengguna belum registrasi"
    assert response["data"] == {"ID Pengguna yang diterima": {user_id}}

@pytest.mark.asyncio
async def test_status_user_success():
    user_id = "testuser"
    response = await status_user_handler(user_id)

    assert response["status_code"] == 200
    assert response["success"] is True
    assert "pengguna sudah registrasi" in response["msg"]
    assert "ID Pengguna yang diterima" in response["data"]

@pytest.mark.asyncio
async def test_status_user_notexist():
    user_id = "hayoyo"
    response = await status_user_handler(user_id)

    assert response["status_code"] == 400
    assert response["success"] is False
    assert "pengguna belum registrasi" in response["msg"]
    assert "ID Pengguna yang diterima" in response["data"]

@pytest.mark.asyncio
async def test_status_user_none():
    user_id = None
    response = await status_user_handler(user_id)

    assert response["status_code"] == 400
    assert response["success"] is False
    assert "Pengguna tidak valid" in response["msg"]
    assert "ID Pengguna yang diterima" in response["data"]