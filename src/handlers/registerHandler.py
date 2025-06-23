from fastapi import UploadFile
from typing import List
from src.config import *
from src.services import register_user
from src.utils import response

async def register_user_handler(user_id: str, files: List[UploadFile]):
    try:
        #Validasi pertama, untuk jumlah gambar
        if len(files) != 50:
            return response(
                status_code=400,
                success=False,
                msg="Kesalahan Jumlah Gambar",
                data={"Gambar diterima": len(files)}
                )
        

        #Validasi kedua, untuk user_id
        if not user_id:
            return response(
                status_code=400,
                success=False,
                msg="Pengguna tidak valid",
                data={"ID Pengguna yang diterima": user_id}
            )
        
        #Validasi ketiga, untuk pengecekan user_id
        # embedding_path = os.path.join(EMBEDDING_DIR, user_id)
        # if os.path.exists(embedding_path):
        #     return response(
        #         status_code=400,
        #         success=False,
        #         msg="Pengguna sudah registrasi",
        #         data={"ID Pengguna yang diterima": {user_id}}
        #     )

        #Menjalankan Proses Registrasi
        result = await register_user(user_id, files)
        print(result)

        #Pengecekan hasil registrasi
        if isinstance(result, dict) and not result["success"]:
            return result
        
        #Mengembalikan response ketika berhasil
        return response(
            status_code=200,
            success=True,
            msg="Registrasi Wajah Berhasil",
            data=result.get("data")
            )
    
    except Exception as e:
        return response(
            status_code=500,
            success=False,
            msg="Terjadi kesalahan saat proses registrasi wajah",
            data={"error": str(e)}
        )