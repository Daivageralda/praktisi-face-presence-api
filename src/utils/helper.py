import os

from PIL import Image
from io import BytesIO
from typing import Any, Dict, List
from sklearn.model_selection import train_test_split

from src.config import *


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """
    Mengonversi bytes gambar menjadi objek PIL Image dengan mode RGB.

    Args:
        image_bytes (bytes): Gambar dalam bentuk bytes.

    Returns:
        Image.Image: Objek gambar dalam mode RGB.
    """
    return Image.open(BytesIO(image_bytes)).convert("RGB")


def train_test_split_and_save(
        images_bytes: List[bytes],
        user_id: str,
        test_ratio: float = 0.2
    ) -> List[bytes]:

    try:
        if len(images_bytes) < 2:
            print("❗ Jumlah gambar terlalu sedikit untuk dilakukan split.")
            return []

        train_imgs, test_imgs = train_test_split(images_bytes, test_size=test_ratio, random_state=42)

        test_dir = os.path.join(IMAGE_DIR, user_id)
        os.makedirs(test_dir, exist_ok=True)
        print(f"Menyimpan {len(test_imgs)} gambar test ke {test_dir}")

        for idx, img_bytes in enumerate(test_imgs):
            try:
                img = load_image_from_bytes(img_bytes)
                img.save(os.path.join(test_dir, f"{user_id}_{idx+1}.webp"), format="WEBP")
            except Exception as e:
                print(f"⚠️ Gagal menyimpan gambar ke-{idx+1}: {e}")

        return train_imgs

    except Exception as e:
        print(f"❌ Gagal melakukan split dan simpan test image: {e}")
        return []


def response(
    status_code: int,
    success: bool,
    msg: str,
    data: Any
) -> Dict[str, Any]:
    """
    Membuat format response standar untuk API.

    Args:
        status_code (int): Kode status HTTP.
        success (bool): Status keberhasilan operasi.
        msg (str): Pesan penjelasan.
        data (Any): Data yang dikembalikan (payload).

    Returns:
        Dict[str, Any]: Respon dalam format JSON.
    """
    return {
        "status_code": status_code,
        "success": success,
        "msg": msg,
        "data": data,
    }
