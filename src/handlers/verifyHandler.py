from fastapi import UploadFile

from src.config import *
from src.services import verify_user
from src.utils import response

async def verify_user_handler(user_id: str, file: UploadFile):
    try:
        # Validasi pertama, untuk jumlah gambar
        if file is None:
            return response(
                status_code=400,
                success=False,
                msg="Kesalahan Jumlah Gambar",
                data={"Gambar diterima": len(file)}
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
        embedding_path = os.path.join(EMBEDDING_DIR, f"{user_id}.pkl")
        if not os.path.exists(embedding_path):
            return response(
                status_code=400,
                success=False,
                msg="Pengguna belum registrasi",
                data={"ID Pengguna yang diterima": {user_id}}
            )      
        result = await verify_user(user_id, file)

        #Pengecekan hasil verifikasi
        if isinstance(result, dict) and not result["success"]:
            return result

        #Mengembalikan response ketika berhasil
        return response(
            status_code=200,
            success=True,
            msg="Verifikasi Wajah Berhasil",
            data=result.get("data")
            )
    
    except Exception as e:
        return response(
            status_code=400,
            success=False,
            msg="Terjadi kesalahan saat proses verifikasi wajah",
            data={"error": str(e)}
        )