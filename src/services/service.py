import os
import joblib
import numpy as np
from PIL import Image
from io import BytesIO
from glob import glob
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import confusion_matrix, classification_report
import random

from src.models.facenet import load_model
from src.utils.helper import load_image_from_bytes, train_test_split_and_save, response

interpreter, input_index, output_index = load_model()

def extract_embedding(image_bytes):
    image = Image.open(BytesIO(image_bytes)).resize((160, 160)).convert("RGB")
    img_array = np.asarray(image).astype(np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    interpreter.set_tensor(input_index, img_array)
    interpreter.invoke()
    embedding = interpreter.get_tensor(output_index)
    return embedding[0]

def save_embedding(embedding, user_id):
    try:
        os.makedirs("src/storage/embeddings", exist_ok=True)
        path_model = f"src/storage/embeddings/{user_id}.pkl"
        if embedding:
            joblib.dump(np.array(embedding), path_model)
            return True
    except Exception as e:
        print(f"Error saving embedding: {e}")
    return False

async def register_user(user_id: str, file: List[UploadFile]):
    print(f"[INFO] Registering user: {user_id}, {len(file)} images received")

    if len(file) != 10:
        raise HTTPException(status_code=400, detail=f"Jumlah gambar harus 10, diterima {len(file)}")

    images_bytes = []
    for i, frame in enumerate(file):
        try:
            content = await frame.read()
            images_bytes.append(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error membaca frame {i+1}: {str(e)}")

    train_images = train_test_split_and_save(images_bytes, user_id)
    if not train_images:
        raise HTTPException(status_code=500, detail="❌ Gagal split/simpan data test.")

    embeddings = []
    for content in train_images:
        image = load_image_from_bytes(content)
        image = image.resize((160, 160))
        emb = extract_embedding(image_bytes=content)
        embeddings.append(emb)

    if save_embedding(embeddings, user_id):
        eval_result = evaluate_user(user_id)
        return response(200, True, f"✅ Registrasi berhasil untuk user {user_id}", eval_result)
    else:
        raise HTTPException(status_code=500, detail="❌ Gagal menyimpan embedding.")

def evaluate_user(user_id: str) -> Dict[str, Any]:
    user_test_dir = f"src/storage/test_image/{user_id}"
    if not os.path.exists(user_test_dir):
        raise HTTPException(status_code=404, detail=f"❌ Folder test_image user {user_id} tidak ditemukan.")

    user_test_paths = sorted(glob(os.path.join(user_test_dir, "*.webp")))
    if len(user_test_paths) == 0:
        raise HTTPException(status_code=404, detail="❌ Tidak ada gambar test user ditemukan.")

    all_user_dirs = glob("src/storage/test_image/*")
    other_users = [d for d in all_user_dirs if os.path.basename(d) != user_id]
    other_images = [img for d in other_users for img in glob(os.path.join(d, "*.webp"))]

    if len(other_images) < len(user_test_paths):
        raise HTTPException(status_code=400, detail="❌ Tidak cukup gambar random untuk evaluasi.")

    random_sample_paths = random.sample(other_images, len(user_test_paths))

    combined_paths = user_test_paths + random_sample_paths
    true_labels = [1] * len(user_test_paths) + [0] * len(random_sample_paths)
    predicted_labels = []

    model_path = f"src/storage/embeddings/{user_id}.pkl"
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="❌ Embedding user tidak ditemukan.")

    saved_embeddings = joblib.load(model_path)

    for i, path in enumerate(combined_paths):
        with open(path, "rb") as f:
            image_bytes = f.read()
        image = load_image_from_bytes(image_bytes)
        image = image.resize((160, 160))
        emb = extract_embedding(image_bytes)
        similarity = cosine_similarity([emb], [saved_embeddings])[0][0]
        predicted = 1 if similarity > 0.7 else 0
        predicted_labels.append(predicted)

    cm = confusion_matrix(true_labels, predicted_labels).tolist()
    report = classification_report(true_labels, predicted_labels, target_names=["Fake", "Real"], output_dict=True)

    return {
        "confusion_matrix": cm,
        "classification_report": report
    }

def compare_embedding(user_id: str, image_bytes):
    model_path = f"src/storage/embeddings/{user_id}.pkl"
    if not os.path.exists(model_path):
        return {"status": "error", "message": "User not found"}

    saved_embeddings = joblib.load(model_path)
    input_embedding = extract_embedding(image_bytes)
    similarity = cosine_similarity([input_embedding], [saved_embeddings])[0][0]
    return similarity

async def verify_user(user_id: str, file: UploadFile):
    bytes_data = await file.read()
    similarity_score = compare_embedding(user_id, bytes_data)
    result_label = "Match" if similarity_score > 0.7 else "Not Match"
    return response(200, True, "Hasil verifikasi", {
        "similarity": float(similarity_score),
        "result": result_label
    })