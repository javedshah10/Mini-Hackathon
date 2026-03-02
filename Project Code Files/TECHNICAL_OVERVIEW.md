# Technical Overview — AI Document Verification (Phase 1 Demo)

## 1) System Architecture

Phase 1 is split into **two deployable services**:

- **Frontend (`frontend/app.py`)**: Streamlit operator UI for upload, process trigger, and result viewing.
- **Backend (`backend/main.py`)**: FastAPI API for submission intake, processing orchestration, and result retrieval.

Core infrastructure/services used in this phase:

- **Supabase Storage** for raw document files.
- **Supabase PostgreSQL** for `submissions`, `documents`, `tool_call_events`, and `validation_results`.
- **Tesseract + PDF tooling** for OCR.
- **Groq model** for structured field extraction.
- **GPT-4o** for document classification and orchestration support.
- **Google Vision (placeholder)** for stamp/signature detection.

This separation allows frontend and backend to be developed/deployed independently while maintaining a clear API contract.

---

## 2) Backend API Surface

The backend exposes a small set of endpoints:

- `POST /submit`
  - Validates file type and size.
  - Creates submission metadata.
  - Uploads document to Supabase Storage.
  - Creates `documents` row and returns `submission_id`.
- `POST /process/{submission_id}`
  - Manual trigger path for operator-initiated processing.
  - Executes the same shared pipeline used by polling mode.
- `GET /result/{submission_id}`
  - Returns current submission status, latest validation result, and tool-call events.
- `GET /health`
  - Basic health/status check.

A background scheduler also runs polling mode to process pending submissions automatically.

---

## 3) End-to-End Processing Flow

### Step A — Submission
1. Operator uploads PDF/JPEG/PNG from Streamlit.
2. Backend validates:
   - max size (5MB)
   - supported MIME types
   - supported OCR language (`hin`, `ben`, `tel`)
3. File is uploaded to Supabase Storage and linked to `submissions`/`documents` tables.

### Step B — Processing Trigger
Two trigger modes call the **same** pipeline function:

1. **Manual**: `POST /process/{submission_id}`.
2. **Automatic poller**: every `POLLING_INTERVAL_SECONDS` (default 30s) processes aged `pending` submissions.

### Step C — Tool-Orchestrated Pipeline
The pipeline executes tools in sequence and logs every step to `tool_call_events`:

1. `ocr_tool`
2. `field_extractor_tool`
3. `classifier_tool`
4. `field_validator_tool`
5. `stamp_signature_tool`
6. `audit_logger_tool`
7. `notification_tool` (skipped in Phase 1)
8. `sync_manager_tool` (skipped in Phase 1)
9. `fraud_tamper_tool` (skipped in Phase 1)

On tool failure, pipeline marks submission as `failed` and logs error context.

### Step D — Result Materialization
Final outcome is persisted in `validation_results`, submission status is updated (`passed`, `failed`, or `escalated`), and returned through `GET /result/{submission_id}` for frontend display.

---

## 4) OCR Logic and Performance Optimizations

The OCR module has been tuned for practical Phase 1 performance and robustness:

### 4.1 Digital PDF Fast-Path
- Uses `pdfplumber` to attempt native text extraction first.
- If text is present/readable, OCR is skipped entirely.
- This avoids unnecessary compute and improves latency/accuracy for digital PDFs.

### 4.2 Single-Pass OCR Confidence + Text
- Uses a single `pytesseract.image_to_data(..., output_type=DICT)` pass.
- Reconstructs text tokens from `data["text"]`.
- Computes confidence from valid `data["conf"]` values (ignoring `-1`).
- Reduces duplicate OCR calls vs separate `image_to_string` + `image_to_data` approach.

### 4.3 Lightweight Image Preprocessing (PIL)
Before Tesseract, images are quickly cleaned using:

1. grayscale conversion,
2. median denoising,
3. simple binary threshold.

These low-cost steps typically improve character contrast and OCR quality for noisy scans.

### 4.4 Memory-Safer Scanned PDF Handling
- Scanned PDFs are converted in page **chunks** (`first_page`/`last_page`) instead of loading all pages at once.
- Image objects are closed after use.
- Helps reduce peak RAM usage for larger documents.

### 4.5 Robust I/O and Parsing
- Remote downloads call `raise_for_status()` to fail fast on bad HTTP responses.
- Confidence parsing tolerates malformed values (`try/except`) without crashing OCR.

---

## 5) Validation and Decision Logic

`field_validator_tool` applies deterministic checks:

- `id_number`: required and alphanumeric.
- `date_of_birth`: required format `DD/MM/YYYY`.
- `full_name`: non-null, minimum length.
- extraction confidence threshold: `< 0.6` flagged for review/escalation.

Status logic:

- validation failures -> `failed`
- low extraction confidence -> `escalated`
- otherwise -> `passed`

---

## 6) Data and Auditability

Every tool call writes a `tool_call_events` row with:

- tool name/status,
- confidence (where applicable),
- summarized input/output,
- error details on failure.

This creates a transparent execution trail for debugging, QA, and stakeholder demos.

---

## 7) Frontend Developer Experience

The Streamlit app provides 3 practical views:

1. **Upload** (document + language + submit)
2. **Processing trigger** (manual process button)
3. **Result** (status, extracted fields table, and raw JSON)

`BACKEND_URL` environment wiring keeps frontend deployment independent from backend runtime location.

---

## 8) Operational Notes for Developers

- Install Tesseract language packs for `hin`, `ben`, and `tel`.
- Install Poppler (`poppler-utils`) for scanned PDF image conversion.
- Configure API keys and Supabase variables in backend `.env`.
- Use polling mode as a safety net even when manual trigger is used.

---

## 9) Phase 1 Scope Boundaries

Intentionally simplified in this demo:

- No citizen authentication layer.
- No offline sync mode (logged as skipped).
- No production-grade fraud/tamper CV pipeline (logged as skipped).
- Stamp/signature detection uses placeholder heuristics/API path for demonstration.

These boundaries keep implementation focused while preserving extensibility toward production architecture.
