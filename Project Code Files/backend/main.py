import os
import tempfile
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile

from db import (
    create_document_record,
    create_submission,
    get_result_bundle,
    get_submission_with_document,
    update_submission_status,
    upload_document,
)
from pipeline import run_submission_pipeline
from scheduler import start_scheduler
from tools.ocr_tool import SUPPORTED_LANGUAGES


load_dotenv()
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}
scheduler = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global scheduler
    scheduler = start_scheduler()
    yield
    if scheduler:
        scheduler.shutdown()


app = FastAPI(title="AI Document Verification API", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/submit")
async def submit_document(file: UploadFile = File(...), language: str = "hin") -> dict:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Supported file formats: PDF, JPEG, PNG")
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail="Language not supported in Phase 1. Supported: Hindi, Bengali, Telugu.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Maximum file size is 5MB")

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    submission = create_submission()
    object_name = f"{submission['id']}/{uuid.uuid4()}-{file.filename}"
    public_url = upload_document(tmp_path, object_name, file.content_type)
    document = create_document_record(
        submission_id=submission["id"],
        file_name=file.filename,
        file_type=file.content_type,
        file_url=public_url,
        language=language,
    )
    os.unlink(tmp_path)

    return {"submission_id": submission["id"], "document_id": document["id"], "file_url": public_url}


@app.post("/process/{submission_id}")
def process_submission(submission_id: str) -> dict:
    bundle = get_submission_with_document(submission_id)
    if not bundle.get("submission"):
        raise HTTPException(status_code=404, detail="Submission not found")

    status = bundle["submission"]["status"]
    if status in {"processing", "passed", "failed", "escalated"}:
        return {"submission_id": submission_id, "status": status, "message": "Skipped."}

    update_submission_status(submission_id, "processing")
    result = run_submission_pipeline(submission_id)
    return {"submission_id": submission_id, **result}


@app.get("/result/{submission_id}")
def get_result(submission_id: str) -> dict:
    try:
        return get_result_bundle(submission_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
