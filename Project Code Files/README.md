# AI Document Verification Platform — Phase 1 Demo

## Architecture
- **Frontend:** Streamlit (`frontend/app.py`)
- **Backend:** FastAPI (`backend/main.py`)
- **Storage / DB:** Supabase Storage + PostgreSQL
- **OCR:** Tesseract + pdf2image/pdfplumber PDF branching
- **Field Extraction:** Groq model (`GROQ_MODEL` env override)
- **Orchestration:** GPT-4o-driven pipeline sequence in `backend/pipeline.py`

## Folder Structure
```
Project Code Files/
├── frontend/
├── backend/
├── AI_Document_Verification_PRD.md
└── README.md
```

## Prerequisites
- Python 3.11+
- Tesseract OCR with language packs: `hin`, `ben`, `tel`, `eng`
- Poppler for scanned PDF conversion (`poppler-utils`)

## Backend Setup
```bash
cd Project Code Files/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env .env.local  # optional
```

Set environment variables in `backend/.env`:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `OPENAI_API_KEY`
- `GROQ_API_KEY`
- `GOOGLE_VISION_API_KEY`
- `SUPABASE_BUCKET=documents`
- `POLLING_INTERVAL_SECONDS=30`

Run backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup
```bash
cd Project Code Files/frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set `frontend/.env`:
- `BACKEND_URL=http://localhost:8000`

Run frontend:
```bash
streamlit run app.py
```

## API Endpoints
- `POST /submit`
- `POST /process/{id}`
- `GET /result/{id}`
- `GET /health`

## Demo Notes
- Max upload size: 5MB
- Supported languages: Hindi (`hin`), Bengali (`ben`), Telugu (`tel`), English (`eng`)
- Unsupported language error is explicitly returned
- Poller runs in backend and auto-processes pending submissions older than configured interval
