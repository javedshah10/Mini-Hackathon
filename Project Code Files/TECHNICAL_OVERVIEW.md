# Technical Overview — AI Document Verification (Phase 1 Demo)

## 1) System Architecture

Phase 1 is split into two deployable services:
- **Frontend (`frontend/app.py`)**: Streamlit operator UI.
- **Backend (`backend/main.py`)**: FastAPI API and processing orchestration.

Core services:
- Supabase Storage (document blobs)
- Supabase PostgreSQL (`submissions`, `documents`, `tool_call_events`, `validation_results`)
- Tesseract OCR + PDF tooling
- Groq LLM for field extraction
- GPT-4o for classification
- Google Vision API placeholder for stamp/signature detection

---

## 2) Backend API Surface

- `POST /submit` — validate/upload file; create submission and document rows
- `POST /process/{submission_id}` — manual processing trigger
- `GET /result/{submission_id}` — status + validation + tool event logs
- `GET /health` — service health

Background polling (APScheduler) runs every `POLLING_INTERVAL_SECONDS` and auto-processes aged pending submissions.

---

## 3) End-to-End Processing Flow

1. Upload document (PDF/JPEG/PNG) and language (`hin`, `ben`, `tel`)
2. Save document in Supabase Storage + metadata rows in PostgreSQL
3. Trigger processing manually (`/process`) or automatically via poller
4. Execute tool pipeline and log each tool call event
5. Persist final validation result + submission status

---

## 4) Database Schema (Phase 1 Required)

Schema is documented and included in `backend/schema.sql`.

### `submissions`
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
citizen_id UUID REFERENCES citizens(id),
employee_id UUID REFERENCES employees(id),
department_id UUID REFERENCES departments(id),
channel TEXT DEFAULT 'assisted',
status TEXT DEFAULT 'pending',
created_at TIMESTAMP DEFAULT now()
```

### `documents`
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
submission_id UUID REFERENCES submissions(id),
file_name TEXT,
file_type TEXT,
file_url TEXT,
doc_type TEXT,
quality_score DECIMAL(4,2),
language TEXT,
uploaded_at TIMESTAMP DEFAULT now()
```

### `tool_call_events`
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
submission_id UUID REFERENCES submissions(id),
tool_name TEXT,
status TEXT,
confidence_score DECIMAL(4,2),
input_summary JSONB,
output_summary JSONB,
error_message TEXT,
executed_at TIMESTAMP DEFAULT now()
```

### `validation_results`
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
submission_id UUID REFERENCES submissions(id),
overall_status TEXT,
fraud_flag BOOLEAN DEFAULT false,
duplicate_flag BOOLEAN DEFAULT false,
stamp_valid BOOLEAN DEFAULT false,
field_results JSONB,
created_at TIMESTAMP DEFAULT now()
```

---

## 5) Tool Pipeline Sequence (Corrected)

1. `ocr_tool` (active)
2. `field_extractor_tool` (active)
3. `classifier_tool` (active)
4. `field_validator_tool` (active)
5. `stamp_signature_tool` (active)
6. `fraud_tamper_tool` (skipped in Phase 1; logged)
7. `audit_logger_tool` (active; final active write step)
8. `notification_tool` (skipped in Phase 1; logged)
9. `sync_manager_tool` (skipped in Phase 1; logged)

---

## 6) OCR Logic and Optimizations

- Digital PDF fast-path with `pdfplumber`; skip OCR when native text is present
- Single-pass OCR extraction using `pytesseract.image_to_data(..., output_type=DICT)` for both text and confidence
- Lightweight preprocessing: grayscale + median denoise + threshold
- Chunked scanned-PDF conversion (`first_page`/`last_page`) for lower memory usage
- HTTP download and confidence parsing hardening

`documents.quality_score` is updated from OCR confidence; `documents.doc_type` is updated after classification.

---

## 7) Google Vision Placeholder (Explicit Behavior)

`stamp_signature_tool` uses Google Vision `object_localization` on the document image.
It evaluates object labels for stamp/seal/signature hints and returns:

```json
{
  "stamp_detected": true,
  "signature_detected": false,
  "confidence_score": 0.72,
  "note": "Phase 1 placeholder — Google Vision API. Production will use YOLOv8 + OpenCV."
}
```

`validation_results.stamp_valid` is set to `true` when either `stamp_detected` or `signature_detected` is true.
The tool output is logged to `tool_call_events` as `stamp_signature_tool` with status `success`.

---

## 8) Groq Model Configuration

Field extraction uses:
- Env var: `GROQ_MODEL_NAME`
- Default model: `llama3-groq-70b-8192-tool-use-preview`

This is configured in `backend/tools/field_extractor_tool.py` and exposed in `backend/.env`.

---

## 9) Operational Notes

- Install Tesseract language packs: `hin`, `ben`, `tel`
- Install Poppler (`poppler-utils`) for scanned PDF conversion
- Configure Supabase/OpenAI/Groq/Google credentials in `backend/.env`
- Set scheduler interval:

```env
POLLING_INTERVAL_SECONDS=30
```

---

## 10) Phase 1 Scope Boundaries

- No authentication in demo
- Offline sync is skipped/logged
- Fraud/tamper CV model is skipped/logged
- Stamp/signature remains Google Vision placeholder (production target: YOLOv8 + OpenCV)
