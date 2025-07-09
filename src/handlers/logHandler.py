from src.config import *
from src.utils import response
from src.utils import verify_logger


async def log_user_handler(user_id: str, durasi: float):
    try:
        # Validasi pertama untuk user_id
        if not user_id:
            return response(
                status_code=400,
                success=False,
                msg="Pengguna tidak valid",
                data={"ID Pengguna yang diterima": user_id}
            )
        
        # Validasi kedua untuk durasi
        if not durasi or durasi <= 0:
            return response(
                status_code=400,
                success=False,
                msg="Durasi tidak valid",
                data={"Durasi yang diterima": durasi}
            )
        

        result = await verify_logger(praktikan_id=user_id, durasi=durasi)

        if isinstance(result, dict) and not result["success"]:
            return result    
        
        return response(
            status_code=200,
            success=True,
            msg="Update Data Berhasil",
            data=result.get("data")
            )  


    except Exception as e:
        return response(
            status_code=500,
            success=False,
            msg="Terjadi kesalahan saat proses logging",
            data={"error": str(e)}
        )