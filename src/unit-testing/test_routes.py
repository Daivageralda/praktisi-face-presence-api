import io
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from src.app import apps as app  # Alias 'apps' ke 'app'
import random
client = TestClient(app)

def create_dummy_image_bytes():
    img = Image.effect_noise((160, 160), random.randint(50, 100))
    draw = ImageDraw.Draw(img)
    for _ in range(5):
        x1, y1 = random.randint(0, 159), random.randint(0, 159)
        x2, y2 = random.randint(0, 159), random.randint(0, 159)
        draw.line((x1, y1, x2, y2), fill=random.randint(0, 255), width=2)
    byte_arr = io.BytesIO()
    img.convert("RGB").save(byte_arr, format='WEBP')
    return byte_arr.getvalue()


def test_register_user():
    # Registrasi user dummy untuk evaluasi pembanding
    client.post("/presence-api/v1/register", files=[('file', ('image.webp', create_dummy_image_bytes(), 'image/webp')) for _ in range(10)], data={'user_id': 'otheruser'})

    # Sekarang registrasi user yang diuji
    user_id = "testuser"
    files = [('file', ('image.webp', create_dummy_image_bytes(), 'image/webp')) for _ in range(10)]
    data = {'user_id': user_id}

    response = client.post("/presence-api/v1/register", files=files, data=data)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["msg"] == "Registrasi Wajah Berhasil"
    assert "confusion_matrix" in response.json()["data"]
    assert "classification_report" in response.json()["data"]


def test_verify_user():
    user_id = "testuser"
    file = ('file', ('image.webp', create_dummy_image_bytes(), 'image/webp'))
    data = {'user_id': user_id}

    response = client.post("/presence-api/v1/verify", files=[file], data=data)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["msg"] == "Verifikasi Wajah Berhasil"
    assert "similarity" in response.json()["data"]
    assert "result" in response.json()["data"]
