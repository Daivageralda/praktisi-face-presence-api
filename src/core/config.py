import os
from pathlib import Path
from pydantic import Field
from typing import Dict, List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.logger import logger

load_dotenv()

class Settings(BaseSettings):
    """
    Application configuration settings.

    This class loads configuration from environment variables and sets default values.
    Used throughout the application for centralized configuration management.
    """

    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    EMBEDDING_DIR: Path = BASE_DIR / "src/storage/embeddings"
    IMAGE_DIR: Path = BASE_DIR / "src/storage/test_images"
    DATASET_DIR: Path = BASE_DIR / "src/storage/lfw-dataset"
    MODEL_PATH: Path = BASE_DIR / "src/models/facenet.tflite"
    LOG_PATH: Path = BASE_DIR / "src/logs"

    # Google Sheets credentials and sheet ID
    CREDENTIALS: str = os.getenv("SHEET_CREDS", "")
    SHEET_ID: str = os.getenv("SHEET_ID", "")

    # Image processing configuration
    IMAGE_SIZE: int = 160
    IMAGE_CHANNEL: int = 3
    IMAGE_COUNT: int = 50

    # Embedding and verification threshold
    THRESHOLD: float = 0.6
    EMBEDDING_DIM: int = 128

    # Thread and batch configuration
    MAX_WORKERS: int = 2
    BATCH_SIZE: int = 10
    MEMORY_THRESHOLD: int = 6000  # MB
    GARBAGE_COLLECTION_INTERVAL: int = 10  # seconds
    DELAY: float = 0.1

    # Google Sheet batch flush interval (seconds)
    BATCH_FLUSH_INTERVAL: int = 30

    # Sheet headers and ranges
    SHEET_HEADERS: Dict[str, List[str]] = Field(default_factory=lambda: {
        "verification": ["id_user", "verifikasi berhasil", "verifikasi gagal", "jumlah verifikasi"],
        "registration": ["id_user", "tp", "fp", "tn", "fn", "acc", "pre", "rec"]
    })

    SHEET_RANGES: Dict[str, str] = Field(default_factory=lambda: {
        "verification": "A1:D1",
        "registration": "A1:H1"
    })

    # TensorFlow threading configuration
    TF_INTER_OP_PARALELLISM: int = 2
    TF_INTRA_OP_PARALELLISM: int = 2
    TF_NUM_THREADS: int = 2

    # FastAPI server settings
    API_PORT: int = 8888
    API_WORKERS: int = 1

    # Dataset split ratio
    TEST_RATIO: float = 0.2

    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    model_config = SettingsConfigDict(extra="allow")


# Global settings instance
try:
    settings = Settings()

    # Ensure necessary directories exist
    os.makedirs(settings.EMBEDDING_DIR, exist_ok=True)
    os.makedirs(settings.IMAGE_DIR, exist_ok=True)
    os.makedirs(settings.LOG_PATH, exist_ok=True)
    os.makedirs(Path(settings.CREDENTIALS).parent, exist_ok=True)

    logger.info("Settings loaded and directories ensured.")
except Exception as e:
    logger.exception(f"Failed to load settings: {e}")
    raise