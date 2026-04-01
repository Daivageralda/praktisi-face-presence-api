# Face Recognition Presence System API

A RESTful API for a **facial recognition-based attendance system**, built using **FaceNet** embeddings and **cosine similarity** for identity verification. Developed as part of the Information Systems Practicum (Praktisi) program.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10 |
| Framework | FastAPI |
| ML Model | TensorFlow Lite (FaceNet) |
| Similarity | scikit-learn (Cosine Similarity) |
| Logging | Google Sheets API (gspread) |
| Containerization | Docker + Docker Compose |
| Image Processing | Pillow |
| Config | pydantic-settings, python-dotenv |

---

## How It Works

1. **Registration** — A user submits 50 face images. The system extracts 128-dimensional FaceNet embeddings from each image and stores them as a `.pkl` file.
2. **Verification** — A single face image is submitted. Its embedding is compared against the stored embeddings using **cosine similarity**. A match is determined by a configurable threshold (default: `0.6`).
3. **Logging** — Attendance events and evaluation metrics are batch-flushed to a **Google Sheets** document at a configurable interval.

```
  User Image
      │
      ▼
  Preprocessing (resize 160×160, normalize)
      │
      ▼
  FaceNet TFLite Model
      │
      ▼
  128-dim Embedding
      │
      ▼
  Cosine Similarity ←── Stored Embeddings (.pkl)
      │
      ▼
  Match / No Match (threshold: 0.6)
```

---

## Project Structure

```
.
├── main.py                     # Entry point (Uvicorn runner)
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── .env.example
└── src/
    ├── app.py                  # FastAPI app instance & middleware
    ├── routes/
    │   └── route.py            # API route definitions
    ├── handlers/               # Request handlers (register, verify, status, log)
    ├── services/               # Business logic (embedding comparison, evaluation)
    ├── models/
    │   ├── facenet.py          # Thread-safe TFLite model loader (singleton)
    │   └── facenet.tflite      # FaceNet model file
    ├── utils/                  # Embedding I/O, image processing, spreadsheet client
    ├── core/                   # Config, logger, thread executor
    ├── storage/
    │   └── embeddings/         # Stored user embeddings (.pkl files)
    ├── logs/                   # Application logs
    └── testing/                # pytest test suite
```

---

## API Endpoints

Base URL prefix: `/presence-api/v1`

### `POST /register`

Register a new user by uploading 50 face images.

| Field | Type | Description |
|---|---|---|
| `user_id` | `string` (form) | Unique user identifier |
| `file` | `List[UploadFile]` (form) | 50 face images |

**Response:** Registration status with evaluation metrics (accuracy, precision, recall).

---

### `POST /verify`

Verify a user's identity using a single face image.

| Field | Type | Description |
|---|---|---|
| `user_id` | `string` (form) | User identifier |
| `file` | `UploadFile` (form) | Face image |

**Response:** Similarity score and match result (`true` / `false`).

---

### `POST /status`

Check the registration or verification status of a user.

| Field | Type | Description |
|---|---|---|
| `user_id` | `string` (form) | User identifier |

---

### `POST /log`

Log the verification duration for a user (batch-flushed to Google Sheets).

| Field | Type | Description |
|---|---|---|
| `user_id` | `string` (form) | User identifier |
| `durasi` | `float` (form) | Verification duration in seconds |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- Google Sheets API credentials (optional, for attendance logging)

### 1. Clone the repository

```bash
git clone https://github.com/Daivageralda/praktisi-face-presence-api.git
cd praktisi-face-presence-api
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
SHEET_CREDS=path/to/your/google-credentials.json
SHEET_ID=your_google_sheet_id
DEBUG=true
```

### 3. Run locally

```bash
pip install -r requirements.txt
python main.py
```

API will be available at: `http://localhost:8888`  
Swagger docs: `http://localhost:8888/docs`

### 4. Run with Docker

```bash
docker-compose up --build
```

---

## Configuration

Key settings are managed via `src/core/config.py` using `pydantic-settings`:

| Variable | Default | Description |
|---|---|---|
| `API_PORT` | `8888` | Server port |
| `THRESHOLD` | `0.6` | Cosine similarity threshold for face match |
| `IMAGE_COUNT` | `50` | Number of images required for registration |
| `IMAGE_SIZE` | `160` | Input image size (px) for FaceNet |
| `EMBEDDING_DIM` | `128` | FaceNet embedding dimensions |
| `BATCH_FLUSH_INTERVAL` | `30` | Seconds between Google Sheets batch flushes |
| `MAX_WORKERS` | `2` | Thread pool size |
| `DEBUG` | `false` | Enable auto-reload and debug logging |

---

## Running Tests

```bash
pytest src/testing/ -v
```

Generate an HTML report:

```bash
pytest src/testing/ --html=report.html
```

---

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
