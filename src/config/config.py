import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
EMBEDDING_DIR = os.path.join(BASE_DIR,'src/storage/embeddings')
IMAGE_DIR = os.path.join(BASE_DIR,'src/storage/test_images')
IMAGE_SIZE = 160
THRESHOLD = 0.6
IMAGE_COUNT = 50