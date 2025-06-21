import os
import joblib
import numpy as np

from fastapi import UploadFile
from sklearn.metrics.pairwise import cosine_similarity

from src.config import *
from src.models import extract_embedding
from src.utils import response

def compare_embedding(user_id: str, image_bytes):
    try:
        model_path = os.path.join(EMBEDDING_DIR, f"{user_id}.pkl")
        
        if not os.path.exists(model_path):
            return response(
                status_code=404,
                success=False,
                msg=f"Pengguna {user_id} tidak ditemukan.",
                data={}
            )

        embeddings = joblib.load(model_path)
        input_embedding = extract_embedding(image_bytes)
        similarities = cosine_similarity([input_embedding], embeddings)
        similarity = float(np.mean(similarities))
        return similarity
    
    except Exception as e:
        return response(
            status_code=500,
            success=False,
            msg="Terjadi kesalahan internal saat perhitungan cosine similarity",
            data={"error": str(e)}
        )

async def verify_user(user_id: str, file: UploadFile):
    print(f"INFO: Verifying user: {user_id}")
    try:
        bytes_data = await file.read()
        similarity_score = compare_embedding(user_id, bytes_data)

        if isinstance(similarity_score, dict): 
            return similarity_score

        result_label = "Match" if similarity_score > THRESHOLD else "Not Match"
        return response(
            status_code=200,
            success=True,
            msg="Verifikasi berhasil dilakukan",
            data={
            "similarity": float(similarity_score),
            "result": result_label
        })
    except Exception as e:
        return response(
            status_code=500,
            success=False,
            msg="Terjadi kesalahan internal saat verifikasi pengguna",
            data={"error": str(e)}
        )