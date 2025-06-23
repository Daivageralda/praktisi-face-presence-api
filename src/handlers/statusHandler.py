# from fastapi import UploadFile

from src.config import *
# from src.services import status_user
from src.utils import response

async def status_user_handler(user_id: str):
    try:
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
                status_code=200,
                success=True,
                msg="pengguna belum registrasi",
                data={"ID Pengguna yang diterima": {user_id}}
            )      
        else:
            #Mengembalikan response ketika berhasil
            return response(
                status_code=200,
                success=True,
                msg="pengguna sudah registrasi",
                data={"ID Pengguna yang diterima": {user_id}}
                )
    
    except Exception as e:
        return response(
            status_code=400,
            success=False,
            msg="Terjadi kesalahan saat proses verifikasi wajah",
            data={"error": str(e)}
        )