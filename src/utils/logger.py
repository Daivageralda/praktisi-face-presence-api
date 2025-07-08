import gspread
from google.oauth2.service_account import Credentials
from src.utils import response
from src.config import *

# Inisialisasi koneksi ke Google Spreadsheet
def get_worksheet(sheet_name="Presensi"):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(
        CREDENTIALS, scopes=scopes
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(SHEET_ID)
    
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        print()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
        worksheet.append_row(["Id Praktikan", "Presensi Berhasil", "Presensi Gagal", "Jumlah Presensi"])
    return worksheet


async def update_Result(
    praktikan_id: str,
    result_label: str = None,
    durasi: float = None
):
    try:
        ws = get_worksheet()
        headers = ws.row_values(1)
        data = ws.get_all_records()

        verifikasi_ke = None
        updated = False

        for i, row in enumerate(data, start=2):
            if str(row['Id Praktikan']) == str(praktikan_id):
                presensi_berhasil = row.get("Presensi Berhasil", 0)
                presensi_gagal = row.get("Presensi Gagal", 0)
                jumlah_presensi = row.get("Jumlah Presensi", 0)

                if result_label == "Match":
                    presensi_berhasil += 1
                elif result_label == "Not Match":
                    presensi_gagal += 1

                jumlah_presensi = presensi_berhasil + presensi_gagal

                ws.update_cell(i, 2, presensi_berhasil)
                ws.update_cell(i, 3, presensi_gagal)
                ws.update_cell(i, 4, jumlah_presensi)

                if durasi is not None:
                    count_existing = len([h for h in headers if h and h.startswith("Verifikasi ")])
                    new_col = f"Verifikasi {count_existing + 1}"

                    if new_col not in headers:
                        ws.update_cell(1, len(headers) + 1, new_col)
                        headers.append(new_col)

                    col_idx = headers.index(new_col) + 1
                    ws.update_cell(i, col_idx, float(durasi))
                    verifikasi_ke = count_existing + 1

                updated = True
                break

        if not updated:
            new_row = [
                praktikan_id,
                1 if result_label == "Match" else 0,
                1 if result_label == "Not Match" else 0,
                1 if result_label in ("Match", "Not Match") else 0
            ]

            if durasi is not None:
                count_existing = len([h for h in headers if h and h.startswith("Verifikasi ")])
                new_col = f"Verifikasi {count_existing + 1}"

                if new_col not in headers:
                    ws.update_cell(1, len(headers) + 1, new_col)
                    headers.append(new_col)

                while len(new_row) < len(headers):
                    new_row.append("")
                new_row[headers.index(new_col)] = float(durasi)
                verifikasi_ke = count_existing + 1

            ws.append_row(new_row)

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
        return response(
            status_code=500,
            success=False,
            msg="Gagal memperbarui Google Spreadsheet",
            data={"error": str(e)}
        )