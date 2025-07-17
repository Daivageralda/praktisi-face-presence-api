import time
import gspread
import threading
from collections import defaultdict

from src.core import settings, logger

verification_queue = []
duration_queue = []
register_queue = []
duration_dict = defaultdict(list)

lock = threading.Lock()

gc = gspread.service_account(filename=settings.CREDENTIALS)
sh = gc.open_by_key(settings.SHEET_ID)

def get_worksheet(sheet_name: str):
    key = sheet_name.lower()
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()

        if not data or not data[0] or len(data[0]) < len(settings.SHEET_HEADERS.get(key, [])):
            ws.update(settings.SHEET_RANGES.get(key), [settings.SHEET_HEADERS.get(key)])

        return ws
    except Exception as e:
        logger.warning(f"[BatchLogger] Worksheet '{sheet_name}' not found, creating new. Reason: {e}")
        ws = sh.add_worksheet(title=sheet_name, rows="1000", cols="1000")
        ws.update(settings.SHEET_RANGES.get(key), [settings.SHEET_HEADERS.get(key)])
        return ws

def enqueue_duration(user_id: str, duration: float):
    with lock:
        duration_dict[user_id].append(duration)

def enqueue_verification(user_id: str, result: str):
    with lock:
        verification_queue.append((user_id, result))

def enqueue_registration(user_id: str, cm: list):
    if (
        not isinstance(cm, list) or
        len(cm) != 2 or
        not all(isinstance(row, list) and len(row) == 2 for row in cm)
    ):
        raise ValueError("Confusion matrix must be 2x2 list: [[TP, FN], [FP, TN]]")

    tp, fn = cm[0]
    fp, tn = cm[1]

    if not all(isinstance(x, int) for x in [tp, fp, tn, fn]):
        raise ValueError("All confusion matrix elements must be integers")

    with lock:
        register_queue.append((user_id, tp, fp, tn, fn))

def col_letter(col):
    result = ''
    while col:
        col, rem = divmod(col - 1, 26)
        result = chr(65 + rem) + result
    return result

def flush_durations_to_spreadsheet():
    while True:
        time.sleep(10)

        with lock:
            if not duration_dict:
                logger.debug("[BatchLogger] No durations, skip flush")
                continue

            total = sum(len(v) for v in duration_dict.values())
            logger.info(f"[BatchLogger] Flushing durations: {total}")

            ws = get_worksheet("Verification")
            data = ws.get_all_values()
            header = data[0] if data else []
            user_rows = {row[0]: (i + 2, row) for i, row in enumerate(data[1:])}

            existing_durasi_count = len(header) - 4
            max_durasi_len = max((len(durations) for durations in duration_dict.values()), default=0)

            # Tambah header baru jika perlu
            header_updates = []
            for i in range(max_durasi_len):
                col_idx = 5 + existing_durasi_count + i
                if len(header) < col_idx:
                    col = col_letter(col_idx)
                    header_updates.append({
                        "range": f"{col}1",
                        "values": [[f"Verifikasi ke-{col_idx - 4}"]]
                    })

            if header_updates:
                ws.batch_update(header_updates)
                header.extend([f"Verifikasi ke-{i+1}" for i in range(len(header), 4 + existing_durasi_count + max_durasi_len)])
                logger.info(f"[BatchLogger] Added {len(header_updates)} new duration headers")

            # Persiapkan batch data
            batch_requests = []
            new_user_rows = []
            
            for user_id, durations in duration_dict.items():
                if user_id in user_rows:
                    rowidx, existing_row = user_rows[user_id]

                    # Hitung jumlah durasi yang sudah ada di baris ini
                    existing_user_durasi = [
                        cell for cell in existing_row[4:] if cell.strip() != ''
                    ]
                    user_durasi_len = len(existing_user_durasi)

                    for i, durasi in enumerate(durations):
                        col_idx = 5 + user_durasi_len + i  # 1-based index
                        col = col_letter(col_idx)

                        # Tambah header kolom jika belum ada
                        if col_idx > len(header):
                            header.append(f"Verifikasi ke-{col_idx - 4}")
                            header_updates.append({
                                "range": f"{col}1",
                                "values": [[f"Verifikasi ke-{col_idx - 4}"]]
                            })

                        batch_requests.append({
                            "range": f"{col}{rowidx}",
                            "values": [[durasi]]
                        })

                else:
                    # Buat baris baru dengan durasi langsung di belakang kolom ke-4
                    row = [user_id, 0, 0, 0] + [""] * existing_durasi_count + durations
                    new_user_rows.append(row)


            if batch_requests:
                ws.batch_update(batch_requests)
                logger.info(f"[BatchLogger] Updated durations for {len(batch_requests)} cells")

            if new_user_rows:
                ws.append_rows(new_user_rows)
                logger.info(f"[BatchLogger] Appended {len(new_user_rows)} new duration rows")

            duration_dict.clear()

def flush_verification_to_spreadsheet():
    while True:
        time.sleep(settings.BATCH_FLUSH_INTERVAL)

        with lock:
            if not verification_queue:
                logger.debug("[BatchLogger] No verifications, skip flush")
                continue

            logger.info(f"[BatchLogger] Flushing {len(verification_queue)} verifications...")

            ws = get_worksheet("Verification")
            data = ws.get_all_values()
            user_rows = {row[0]: (i + 2, row) for i, row in enumerate(data[1:])}
            existing_user_ids = set(user_rows.keys())
            updated = {}

            for user_id, result in verification_queue:
                if user_id not in updated:
                    updated[user_id] = [0, 0, 0]

                if result == "Match":
                    updated[user_id][0] += 1
                else:
                    updated[user_id][1] += 1

                updated[user_id][2] += 1

            batch_requests = []
            next_empty_row = len(data) + 1

            for user_id, (n_berhasil, n_gagal, n_total) in updated.items():
                if user_id in existing_user_ids:
                    row_idx, row = user_rows[user_id]
                    berhasil = int(row[1]) if len(row) > 1 else 0
                    gagal = int(row[2]) if len(row) > 2 else 0
                    total = int(row[3]) if len(row) > 3 else 0

                    batch_requests.extend([
                        {"range": f"B{row_idx}", "values": [[berhasil + n_berhasil]]},
                        {"range": f"C{row_idx}", "values": [[gagal + n_gagal]]},
                        {"range": f"D{row_idx}", "values": [[total + n_total]]},
                    ])
                else:
                    batch_requests.extend([
                        {"range": f"A{next_empty_row}", "values": [[user_id]]},
                        {"range": f"B{next_empty_row}", "values": [[n_berhasil]]},
                        {"range": f"C{next_empty_row}", "values": [[n_gagal]]},
                        {"range": f"D{next_empty_row}", "values": [[n_total]]},
                    ])
                    next_empty_row += 1

            if batch_requests:
                ws.batch_update(batch_requests)
                logger.info(f"[BatchLogger] Updated verification for {len(updated)} users")

            verification_queue.clear()

def flush_register_to_spreadsheet():
    while True:
        time.sleep(settings.BATCH_FLUSH_INTERVAL)

        with lock:
            if not register_queue:
                logger.debug("[BatchLogger] No registrations, skip flush")
                continue

            logger.info(f"[BatchLogger] Flushing {len(register_queue)} registrations...")

            ws = get_worksheet("Registration")
            data = ws.get_all_values()
            user_rows = {row[0]: (i + 2, row) for i, row in enumerate(data[1:])}

            batch_requests = []
            new_user_rows = []

            for user_id, tp, fp, tn, fn in register_queue:
                total = tp + fp + tn + fn
                acc = (tp + tn) / total if total else 0
                pre = tp / (tp + fp) if (tp + fp) else 0
                rec = tp / (tp + fn) if (tp + fn) else 0

                values = [user_id, tp, fp, tn, fn, round(acc, 4), round(pre, 4), round(rec, 4)]

                if user_id in user_rows:
                    row_idx, _ = user_rows[user_id]
                    batch_requests.append({
                        "range": f"A{row_idx}:H{row_idx}",
                        "values": [values]
                    })
                else:
                    new_user_rows.append(values)

            if batch_requests:
                ws.batch_update(batch_requests)
                logger.info(f"[BatchLogger] Updated {len(batch_requests)} registration rows")

            if new_user_rows:
                ws.append_rows(new_user_rows)
                logger.info(f"[BatchLogger] Appended {len(new_user_rows)} new registration rows")

            register_queue.clear()

def start_spreadsheet():
    """Start all logger threads for background flush"""
    threading.Thread(target=flush_verification_to_spreadsheet, daemon=True).start()
    threading.Thread(target=flush_durations_to_spreadsheet, daemon=True).start()
    threading.Thread(target=flush_register_to_spreadsheet, daemon=True).start()
    logger.info("[BatchLogger] Background loggers started")
