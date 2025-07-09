from typing import List
from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager

from src.config import *
from src.utils import response

def get_creds():
    return Credentials.from_service_account_file(
        CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

# Global Variable
agcm = AsyncioGspreadClientManager(get_creds)

async def get_worksheet(sheet_name):
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(SHEET_ID)
    
    try:
        worksheet = await spreadsheet.worksheet(sheet_name)
    except:
        worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
        if sheet_name == "Presensi":
            await worksheet.append_row(["Id Praktikan", "Presensi Berhasil", "Presensi Gagal", "Jumlah Presensi"])
        elif sheet_name == "Registrasi":
            await worksheet.append_row(["Id Praktikan", "Akurasi", "Presisi", "Recall"])
    return worksheet

async def verify_logger(praktikan_id: str, result_label: str = None, durasi: float = None, sheet_name = "Presensi"):
    try:
        ws = await get_worksheet(sheet_name)
        headers = await ws.row_values(1)
        data = await ws.get_all_records()
        verifikasi_ke = None
        updated = False

        for i, row in enumerate(data, start=2):
            if str(row['Id Praktikan']) == str(praktikan_id):
                berhasil = row.get("Presensi Berhasil", 0)
                gagal = row.get("Presensi Gagal", 0)

                if result_label == "Match":
                    berhasil += 1
                elif result_label == "Not Match":
                    gagal += 1

                jumlah = berhasil + gagal

                await ws.update_cell(i, 2, berhasil)
                await ws.update_cell(i, 3, gagal)
                await ws.update_cell(i, 4, jumlah)

                if durasi is not None:
                    count_existing = len([h for h in headers if h.startswith("Verifikasi ")])
                    new_col = f"Verifikasi {count_existing + 1}"
                    if new_col not in headers:
                        await ws.update_cell(1, len(headers) + 1, new_col)
                        headers.append(new_col)

                    col_idx = headers.index(new_col) + 1
                    await ws.update_cell(i, col_idx, float(durasi))
                    verifikasi_ke = count_existing + 1

                updated = True
                break

        if not updated:
            new_row = [
                praktikan_id,
                1 if result_label == "Match" else 0,
                1 if result_label == "Not Match" else 0,
                1
            ]

            if durasi is not None:
                count_existing = len([h for h in headers if h.startswith("Verifikasi ")])
                new_col = f"Verifikasi {count_existing + 1}"
                if new_col not in headers:
                    await ws.update_cell(1, len(headers) + 1, new_col)
                    headers.append(new_col)

                while len(new_row) < len(headers):
                    new_row.append("")
                new_row[headers.index(new_col)] = float(durasi)

            await ws.append_row(new_row)

        return response(
            status_code=200,
            success=True,
            msg="Berhasil memperbarui presensi",
            data={
                "praktikan_id": praktikan_id,
                "hasil": result_label,
                "durasi": durasi,
                "verifikasi_ke": verifikasi_ke,
            }
        )

    except Exception as e:
        return response(500, False, "Gagal update presensi", {"error": str(e)})

async def register_logger(praktikan_id: str, cm: List[List[int]], sheet_name="Registrasi"):
    try:
        ws = await get_worksheet(sheet_name)
        data = await ws.get_all_records()

        TP, TN, FP, FN = cm[1][1], cm[0][0], cm[0][1], cm[1][0]
        total = TP + TN + FP + FN
        akurasi = (TP + TN) / total if total else 0
        presisi = TP / (TP + FP) if (TP + FP) else 0
        recall = TP / (TP + FN) if (TP + FN) else 0

        updated = False
        for i, row in enumerate(data, start=2):
            if str(row.get("Id Praktikan")) == str(praktikan_id):
                await ws.update_cell(i, 2, round(akurasi, 4))
                await ws.update_cell(i, 3, round(presisi, 4))
                await ws.update_cell(i, 4, round(recall, 4))
                updated = True
                break

        if not updated:
            await ws.append_row([
                praktikan_id,
                round(akurasi, 4),
                round(presisi, 4),
                round(recall, 4)
            ])

        return response(200, True, "Berhasil catat evaluasi", {
            "praktikan_id": praktikan_id,
            "akurasi": akurasi,
            "presisi": presisi,
            "recall": recall
        })
    
    except Exception as e:
        return response(500, False, "Gagal catat evaluasi", {"error": str(e)})