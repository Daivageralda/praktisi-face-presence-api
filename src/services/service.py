# import os
# import joblib
# import numpy as np
# from PIL import Image
# from io import BytesIO
# from glob import glob
# from typing import List, Dict, Any
# from fastapi import UploadFile, HTTPException
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.metrics import confusion_matrix, classification_report
# import random

# from src.config import *
# from src.models import load_model
# from src.utils import load_image_from_bytes, train_test_split_and_save, response

# interpreter, input_index, output_index = load_model()

# def extract_embedding(image_bytes):
#     image = Image.open(BytesIO(image_bytes)).resize((160, 160)).convert("RGB")
#     img_array = np.asarray(image).astype(np.float32) / 255.0
#     img_array = np.expand_dims(img_array, axis=0)
#     interpreter.set_tensor(input_index, img_array)
#     interpreter.invoke()
#     embedding = interpreter.get_tensor(output_index)
#     return embedding[0]

# def save_embedding(embedding, user_id):
#     try:
#         if not embedding or not isinstance(embedding, (list, np.ndarray)):
#             print("Embedding tidak valid atau kosong.")
#             return False

#         os.makedirs(EMBEDDING_DIR, exist_ok=True)
#         path_model = os.path.join(EMBEDDING_DIR, f"{user_id}.pkl")
#         joblib.dump(np.array(embedding), path_model)
#         print(f"✅ Embedding berhasil disimpan: {path_model}")
#         return True

#     except Exception as e:
#         print(f"Error saving embedding untuk user {user_id}: {e}")
#         return False



# async def register_user(user_id: str, file: List[UploadFile]):
#     print(f"[INFO] Registering user: {user_id}")

#     #Tahap 1, Baca dan Simpan Bytes Gambar ke Dalam Sebuah Variabel
#     images_bytes = []
#     for i, frame in enumerate(file):
#         try:
#             content = await frame.read()
#             images_bytes.append(content)
#         except Exception as e:
#             return response(
#                 status_code=400,
#                 success=False,
#                 msg="Terjadi kesalahan saat memproses gambar",
#                 data={"error": str(e)}
#             )

#     # Tahap 2, Spltting Data menjadi TRAIN DAN TEST Dengan Proporsi 80:20
#     try:
#         train_images = train_test_split_and_save(images_bytes, user_id)
#         if not train_images:
#             return response(
#                 status_code=500,
#                 success=False,
#                 msg="Gagal menyimpan gambar hasil split",
#                 data={}
#             )

#     except Exception as e:
#         return response(
#             status_code=500,
#             success=False,
#             msg="Terjadi kesalahan saat proses split data",
#             data={"error": str(e)}
#         )

        
#     # Tahap 3, Ekstraksi dan Simpan Embedding Data Train Dalam Sebuah Variabel
#     embeddings = []
#     for content in train_images:
#         try:
#             image = load_image_from_bytes(content)
#             image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
#             emb = extract_embedding(image_bytes=content)
#             embeddings.append(emb)
#         except Exception as e:
#             return response(
#                 status_code=500,
#                 success=False,
#                 msg="Terjadi kesalahan saat proses ekstrak embedding",
#                 data={"error": str(e)}
#             )


#     # Tahap 4, Simpan Embedding Berdasarkan ID Pengguna dan Lakukan Evaluasi
#     try:
#         if save_embedding(embeddings, user_id):
#             eval_result = evaluate_user(user_id)
#             return eval_result
        
#     except Exception as e:
#         return response(
#             status_code=500,
#             success=False,
#             msg="Terjadi kesalahan saat simpan dan evaluasi",
#             data={"error": str(e)}
#         )


# def evaluate_user(user_id: str) -> Dict[str, Any]:
#     try:
#         user_test_dir = os.path.join(IMAGE_DIR, user_id)
        
#         if not os.path.exists(user_test_dir):
#             return response(
#                 status_code=404,
#                 success=False,
#                 msg=f"❌ Folder test_image user {user_id} tidak ditemukan.",
#                 data={}
#             )

#         user_test_paths = sorted(glob(os.path.join(user_test_dir, "*.webp")))
#         if len(user_test_paths) == 0:
#             return response(
#                 status_code=404,
#                 success=False,
#                 msg="❌ Tidak ada gambar test user ditemukan.",
#                 data={}
#             )

#         all_user_dirs = glob(os.path.join(IMAGE_DIR, "*"))
#         other_users = [d for d in all_user_dirs if os.path.basename(d) != user_id]
#         other_images = [img for d in other_users for img in glob(os.path.join(d, "*.webp"))]

#         if len(other_images) < len(user_test_paths):
#             return response(
#                 status_code=400,
#                 success=False,
#                 msg="❌ Tidak cukup gambar random dari user lain untuk evaluasi.",
#                 data={"jumlah_tersedia": len(other_images)}
#             )

#         random_sample_paths = random.sample(other_images, len(user_test_paths))
#         combined_paths = user_test_paths + random_sample_paths
#         true_labels = [1] * len(user_test_paths) + [0] * len(random_sample_paths)
#         predicted_labels = []

#         embed_path = os.path.join(EMBEDDING_DIR, f"{user_id}.pkl")
#         if not os.path.exists(embed_path):
#             return response(
#                 status_code=404,
#                 success=False,
#                 msg="❌ Embedding user tidak ditemukan.",
#                 data={}
#             )

#         saved_embeddings = joblib.load(embed_path)

#         for i, path in enumerate(combined_paths):
#                 try:
#                     with open(path, "rb") as f:
#                         image_bytes = f.read()
#                     image = load_image_from_bytes(image_bytes)
#                     image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
#                     emb = extract_embedding(image_bytes)
#                     similarity = cosine_similarity([emb], saved_embeddings)[0][0]
#                     predicted = 1 if similarity > THRESHOLD else 0
#                     predicted_labels.append(predicted)
#                 except Exception as e:
#                     predicted_labels.append(0)  # Default fallback
#                     print(f"❗ Gagal evaluasi gambar: {path} | Error: {e}")

#         cm = confusion_matrix(true_labels, predicted_labels).tolist()
#         report = classification_report(
#             true_labels,
#             predicted_labels,
#             target_names=["Fake", "Real"],
#             output_dict=True
#         )

#         return response(
#             status_code=200,
#             success=True,
#             msg="Evaluasi user berhasil dilakukan",
#             data={
#                 "confusion_matrix": cm,
#                 "classification_report": report
#             }
#         )
#     except Exception as e:
#         return response(
#             status_code=500,
#             success=False,
#             msg="❌ Terjadi kesalahan internal saat evaluasi user",
#             data={"error": str(e)}
#         )

# def compare_embedding(user_id: str, image_bytes):
#     try:
#         model_path = os.path.join(EMBEDDING_DIR, f"{user_id}.pkl")
        
#         if not os.path.exists(model_path):
#             return response(
#                 status_code=404,
#                 success=False,
#                 msg=f"Pengguna {user_id} tidak ditemukan.",
#                 data={}
#             )

#         embeddings = joblib.load(model_path)
#         input_embedding = extract_embedding(image_bytes)
#         similarities = cosine_similarity([input_embedding], embeddings)
#         similarity = float(np.mean(similarities))
#         return similarity
    
#     except Exception as e:
#         return response(
#             status_code=500,
#             success=False,
#             msg="Terjadi kesalahan internal saat perhitungan cosine similarity",
#             data={"error": str(e)}
#         )

# async def verify_user(user_id: str, file: UploadFile):
#     try:
#         bytes_data = await file.read()
#         similarity_score = compare_embedding(user_id, bytes_data)

#         if isinstance(similarity_score, dict): 
#             return response(
#                 status_code=400,
#                 success=False,
#                 msg="Pengguna tidak valid",
#                 data=similarity_score)

#         result_label = "Match" if similarity_score > THRESHOLD else "Not Match"
#         return response(
#             status_code=200,
#             success=True,
#             msg="Verifikasi berhasil dilakukan",
#             data={
#             "similarity": float(similarity_score),
#             "result": result_label
#         })
#     except Exception as e:
#         return response(
#             status_code=500,
#             success=False,
#             msg="❌ Terjadi kesalahan internal saat verifikasi pengguna",
#             data={"error": str(e)}
#         )