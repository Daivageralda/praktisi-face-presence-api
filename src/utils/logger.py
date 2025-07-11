import time
import asyncio

from typing import List
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from gspread_asyncio import AsyncioGspreadClientManager

from src.config import *
from src.utils import response

def get_creds():
    return Credentials.from_service_account_file(
        CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

# Global Variables dengan caching
agcm = AsyncioGspreadClientManager(get_creds)
_cached_worksheets = {} 
_cached_data = {}
_cache_expiry = {} 
_connection_pool = None
_is_warming_up = False

CACHE_DURATION = 30 #seconds

async def warm_up_connection():
    """Warm up connection di background"""
    global _connection_pool, _is_warming_up
    if _is_warming_up:
        return
    
    _is_warming_up = True
    try:
        # Pre-authorize connection
        agc = await agcm.authorize()
        spreadsheet = await agc.open_by_key(SHEET_ID)
        
        # Pre-load worksheet objects
        try:
            presensi_ws = await spreadsheet.worksheet("Presensi")
            registrasi_ws = await spreadsheet.worksheet("Registrasi")
            
            _cached_worksheets["Presensi"] = presensi_ws
            _cached_worksheets["Registrasi"] = registrasi_ws
            
            # Pre-load data
            presensi_data = await presensi_ws.get_all_records()
            presensi_headers = await presensi_ws.row_values(1)
            
            _cached_data["Presensi"] = {
                "data": presensi_data,
                "headers": presensi_headers,
                "timestamp": datetime.now()
            }
            
            print(f"Connection warmed up successfully at {datetime.now()}")
            
        except Exception as e:
            print(f"Worksheet not found during warm-up: {e}")
            
        _connection_pool = agc
        
    except Exception as e:
        print(f"Warm-up failed: {e}")
    finally:
        _is_warming_up = False

async def get_worksheet(sheet_name, use_cache=True):
    """Get worksheet dengan caching dan connection pooling"""
    global _connection_pool
    
    # Jika cache belum expired
    if use_cache and sheet_name in _cached_worksheets:
        return _cached_worksheets[sheet_name]
    
    if _connection_pool:
        agc = _connection_pool
    else:
        agc = await agcm.authorize()
        _connection_pool = agc
    
    spreadsheet = await agc.open_by_key(SHEET_ID)
    
    try:
        worksheet = await spreadsheet.worksheet(sheet_name)
    except:
        worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="100")
        if sheet_name == "Presensi":
            await worksheet.append_row(["Id Praktikan", "Presensi Berhasil", "Presensi Gagal", "Jumlah Presensi"])
        elif sheet_name == "Registrasi":
            await worksheet.append_row(["Id Praktikan", "Akurasi", "Presisi", "Recall"])
    
    # Cache worksheet
    _cached_worksheets[sheet_name] = worksheet
    return worksheet

async def get_cached_data(sheet_name):
    """Get data dengan caching mechanism"""
    now = datetime.now()
    cache_key = sheet_name
    
    # Check if cache exists and is still valid
    if (cache_key in _cached_data and 
        cache_key in _cache_expiry and 
        now < _cache_expiry[cache_key]):
        return _cached_data[cache_key]
    
    # Cache expired or doesn't exist, fetch fresh data
    ws = await get_worksheet(sheet_name)
    all_data = await ws.get_all_records()
    headers = await ws.row_values(1)
    
    # Update cache
    _cached_data[cache_key] = {
        "data": all_data,
        "headers": headers,
        "timestamp": now
    }
    _cache_expiry[cache_key] = now + timedelta(seconds=CACHE_DURATION)
    
    return _cached_data[cache_key]

def invalidate_cache(sheet_name):
    """Invalidate cache setelah update"""
    if sheet_name in _cached_data:
        del _cached_data[sheet_name]
    if sheet_name in _cache_expiry:
        del _cache_expiry[sheet_name]

def get_column_letter(n):
    """Convert number to Excel-style column letter"""
    result = ''
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

async def verify_logger(praktikan_id: str, result_label: str = None, durasi: float = None, sheet_name = "Presensi"):
    """Optimized verify_logger dengan caching dan connection pooling"""
    start_time = time.time()
    
    try:
        # Warm up connection
        if not _connection_pool and not _is_warming_up:
            asyncio.create_task(warm_up_connection())
        
        # Get cached data
        cached_result = await get_cached_data(sheet_name)
        all_data = cached_result["data"]
        headers = cached_result["headers"].copy()
        
        ws = await get_worksheet(sheet_name)
        
        verifikasi_ke = None
        updated = False
        row_index = None
        
        # Cari praktikan di data yang sudah ada
        for i, row in enumerate(all_data):
            if str(row.get('Id Praktikan', '')) == str(praktikan_id):
                row_index = i + 2 #Skip header (row 1)
                updated = True
                break
        
        # Prepare batch updates
        batch_updates = []
        
        if updated:
            # Update existing row
            current_row = all_data[row_index - 2]  # -2 untuk mendapatkan index yang benar
            berhasil = current_row.get("Presensi Berhasil", 0)
            gagal = current_row.get("Presensi Gagal", 0)
            
            if result_label == "Match":
                berhasil += 1
            elif result_label == "Not Match":
                gagal += 1
            
            jumlah = berhasil + gagal
            
            # Simultaneous columns update
            batch_updates.append({
                'range': f'B{row_index}:D{row_index}',
                'values': [[berhasil, gagal, jumlah]]
            })
            
            # Duration columns update
            if durasi is not None:
                count_existing = len([h for h in headers if h.startswith("Verifikasi ")])
                new_col = f"Verifikasi {count_existing + 1}"
                verifikasi_ke = count_existing + 1
                
                if new_col not in headers:
                    # Add new column header
                    col_letter = get_column_letter(len(headers) + 1)
                    batch_updates.append({
                        'range': f'{col_letter}1',
                        'values': [[new_col]]
                    })

                    headers.append(new_col)
                
                # Add durasi value
                col_letter = get_column_letter(headers.index(new_col) + 1)
                batch_updates.append({
                    'range': f'{col_letter}{row_index}',
                    'values': [[float(durasi)]]
                })
        
        else:
            # Add new row
            new_row = [
                praktikan_id,
                1 if result_label == "Match" else 0,
                1 if result_label == "Not Match" else 0,
                1
            ]
            
            if durasi is not None:
                count_existing = len([h for h in headers if h.startswith("Verifikasi ")])
                new_col = f"Verifikasi {count_existing + 1}"
                verifikasi_ke = count_existing + 1
                
                if new_col not in headers:
                    # Add new column header
                    batch_updates.append({
                        'range': f'{chr(65 + len(headers))}1',
                        'values': [[new_col]]
                    })
                    headers.append(new_col)
                
                # Extend new_row to match headers length
                while len(new_row) < len(headers):
                    new_row.append("")
                
                new_row[headers.index(new_col)] = float(durasi)
            
            # Add the new row
            batch_updates.append({
                'range': f'A{len(all_data) + 2}',  # +2 for header + 1-based indexing
                'values': [new_row]
            })
        
        # Execute all updates in one batch request
        if batch_updates:
            await ws.batch_update(batch_updates)
        
        # Invalidate cache setelah update
        invalidate_cache(sheet_name)
        
        execution_time = time.time() - start_time
        
        return response(
            status_code=200,
            success=True,
            msg="Berhasil memperbarui presensi",
            data={
                "praktikan_id": praktikan_id,
                "hasil": result_label,
                "durasi": durasi,
                "verifikasi_ke": verifikasi_ke,
                "execution_time": execution_time
            }
        )

    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ verify_logger failed in {execution_time:.2f}s: {e}")
        return response(500, False, "Gagal update presensi", {"error": str(e)})

async def register_logger(praktikan_id: str, cm: List[List[int]], sheet_name="Registrasi"):
    """Optimized register_logger dengan caching"""
    start_time = time.time()
    
    try:
        # Warm up connection
        if not _connection_pool and not _is_warming_up:
            asyncio.create_task(warm_up_connection())
        
        # Get cached data
        cached_result = await get_cached_data(sheet_name)
        all_data = cached_result["data"]
        
        ws = await get_worksheet(sheet_name)

        TP, TN, FP, FN = cm[1][1], cm[0][0], cm[0][1], cm[1][0]
        total = TP + TN + FP + FN
        akurasi = (TP + TN) / total if total else 0
        presisi = TP / (TP + FP) if (TP + FP) else 0
        recall = TP / (TP + FN) if (TP + FN) else 0

        updated = False
        row_index = None
        
        # Cari praktikan di data yang sudah ada
        for i, row in enumerate(all_data):
            if str(row.get("Id Praktikan", "")) == str(praktikan_id):
                row_index = i + 2  # +2 karena enumerate mulai dari 0, dan row 1 adalah header
                updated = True
                break

        if updated:
            # Update existing row
            await ws.batch_update([{
                'range': f'B{row_index}:D{row_index}',
                'values': [[round(akurasi, 4), round(presisi, 4), round(recall, 4)]]
            }])
        else:
            # Add new row
            await ws.append_row([
                praktikan_id,
                round(akurasi, 4),
                round(presisi, 4),
                round(recall, 4)
            ])

        # Invalidate cache after update
        invalidate_cache(sheet_name)
        
        execution_time = time.time() - start_time
        print(f"⚡ register_logger executed in {execution_time:.2f}s")

        return response(200, True, "Berhasil catat evaluasi", {
            "praktikan_id": praktikan_id,
            "akurasi": akurasi,
            "presisi": presisi,
            "recall": recall,
            "execution_time": execution_time
        })
    
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"register_logger failed in {execution_time:.2f}s: {e}")
        return response(500, False, "Gagal catat evaluasi", {"error": str(e)})

async def initialize_sheets_connection():
    """Function untuk dipanggil saat startup aplikasi"""
    await warm_up_connection()

async def periodic_refresh():
    """Background task untuk refresh connection secara berkala"""
    while True:
        await asyncio.sleep(300)  # 5 menit
        try:
            await warm_up_connection()
        except Exception as e:
            print(f"Periodic refresh failed: {e}")