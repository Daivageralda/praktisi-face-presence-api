from typing import Any, Dict, List
from PIL import Image
from io import BytesIO
import os
from sklearn.model_selection import train_test_split


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
    """
    Membagi gambar menjadi data pelatihan dan pengujian, serta menyimpan gambar uji ke file .webp.

    Args:
        images_bytes (List[bytes]): Daftar gambar dalam bentuk bytes.
        user_id (str): ID pengguna.
        test_ratio (float): Rasio pembagian data test. Default 0.2.

    Returns:
        List[bytes]: Gambar hasil pembagian training (tanpa yang test).
    """
    try:
        # Split menjadi data train dan test
        train_imgs, test_imgs = train_test_split(images_bytes, test_size=test_ratio, random_state=42)

        # Direktori penyimpanan gambar test
        test_dir = os.path.join("src", "storage", "test_images", user_id)
        os.makedirs(test_dir, exist_ok=True)

        # Simpan setiap gambar test sebagai .webp
        for idx, img_bytes in enumerate(test_imgs):
            img = load_image_from_bytes(img_bytes)
            img.save(os.path.join(test_dir, f"test_{idx+1}.webp"), format="WEBP")

        return train_imgs  # hanya train_imgs yang digunakan untuk proses embedding
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
