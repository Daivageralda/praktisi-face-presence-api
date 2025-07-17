import os
import gc

from PIL import Image
from io import BytesIO
from typing import Any, Dict, List
from sklearn.model_selection import train_test_split

from src.core import logger, settings

def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """
    Load image from raw bytes with RGB conversion if needed.
    Optimized for memory usage.
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image
    except Exception as e:
        logger.exception("❌ Error loading image from bytes")
        raise


def train_test_split_and_save(
    images_bytes: List[bytes],
    user_id: str,
    test_ratio: float = settings.TEST_RATIO
) -> List[bytes]:
    """
    Split image bytes into train/test and save test images to disk.
    Returns only the train image bytes.
    """
    try:
        if len(images_bytes) < 2:
            logger.warning("❗ Jumlah gambar terlalu sedikit untuk dilakukan split.")
            return []

        # Split data
        train_imgs, test_imgs = train_test_split(
            images_bytes,
            test_size=test_ratio,
            random_state=42
        )

        # Setup path
        test_dir = os.path.join(settings.IMAGE_DIR, user_id)
        os.makedirs(test_dir, exist_ok=True)

        saved_count = 0
        for idx, img_bytes in enumerate(test_imgs):
            try:
                img = load_image_from_bytes(img_bytes)
                img = img.resize((settings.IMAGE_SIZE, settings.IMAGE_SIZE), Image.Resampling.LANCZOS)

                output_path = os.path.join(test_dir, f"{user_id}_{idx+1}.webp")
                img.save(output_path, format="WEBP", quality=85, optimize=True)
                img.close()
                saved_count += 1

                if idx % settings.GARBAGE_COLLECTION_INTERVAL == 0:
                    clear_memory()

            except Exception as e:
                logger.error(f"⚠️ Gagal menyimpan gambar ke-{idx+1} untuk user {user_id}: {e}")

        logger.info(f"📁 {saved_count} test image berhasil disimpan untuk user {user_id} di {test_dir}")
        clear_memory()
        return train_imgs

    except Exception as e:
        logger.exception("❌ Gagal melakukan split dan simpan test image")
        return []


def response(status_code: int, success: bool, msg: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardized API response format.
    """
    return {
        "status_code": status_code,
        "success": success,
        "message": msg,
        "data": data
    }


def clear_memory() -> None:
    """Force garbage collection"""
    gc.collect()
    logger.debug("🧹 Memory cleared with garbage collector.")
