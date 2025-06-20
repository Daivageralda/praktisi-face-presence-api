import os

BASE_DIR = f"F:/Kuliah/Skripsi/praktisi-face-presence-api"
EMBEDDING_DIR = os.path.join(BASE_DIR,'src/storage/embeddings')
IMAGE_DIR = os.path.join(BASE_DIR,'src/storage/test_images')
IMAGE_SIZE = 160
THRESHOLD = 0.6
IMAGE_COUNT = 50