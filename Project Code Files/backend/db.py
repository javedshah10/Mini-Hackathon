import json
import os
from typing import Any, Dict, Optional

from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "documents")


if not SUPABASE_URL or not SUPABASE_KEY:
    supabase: Optional[Client] = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase() -> Client:
    if supabase is None:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    return supabase


def create_submission(
    department_id: Optional[str] = None,
    channel: str = "assisted",
    citizen_id: Optional[str] = None,
    employee_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"channel": channel, "status": "pending"}
    if department_id:
        payload["department_id"] = department_id
    if citizen_id:
        payload["citizen_id"] = citizen_id
    if employee_id:
        payload["employee_id"] = employee_id
    response = get_supabase().table("submissions").insert(payload).execute()
    return response.data[0]


def create_document_record(
    submission_id: str,
    file_name: str,
    file_type: str,
    file_url: str,
    language: str,
) -> Dict[str, Any]:
    payload = {
        "submission_id": submission_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_url": file_url,
        "language": language,
    }
    response = get_supabase().table("documents").insert(payload).execute()
    return response.data[0]


def upload_document(file_path: str, file_name: str, content_type: str) -> str:
    client = get_supabase()
    with open(file_path, "rb") as f:
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=file_name,
            file=f,
            file_options={"content-type": content_type, "upsert": "true"},
        )
    return client.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)




def update_document_analysis(submission_id: str, quality_score: float, doc_type: Optional[str] = None) -> None:
    payload: Dict[str, Any] = {"quality_score": round(float(quality_score), 2)}
    if doc_type:
        payload["doc_type"] = doc_type
    get_supabase().table("documents").update(payload).eq("submission_id", submission_id).execute()

def log_tool_event(
    submission_id: str,
    tool_name: str,
    status: str,
    confidence_score: Optional[float] = None,
    input_summary: Optional[Dict[str, Any]] = None,
    output_summary: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
) -> None:
    payload = {
        "submission_id": submission_id,
        "tool_name": tool_name,
        "status": status,
        "confidence_score": confidence_score,
        "input_summary": input_summary or {},
        "output_summary": output_summary or {},
        "error_message": error_message,
    }
    get_supabase().table("tool_call_events").insert(payload).execute()


def update_submission_status(submission_id: str, status: str) -> None:
    get_supabase().table("submissions").update({"status": status}).eq("id", submission_id).execute()


def upsert_validation_result(
    submission_id: str,
    overall_status: str,
    field_results: Dict[str, Any],
    stamp_valid: bool,
    fraud_flag: bool = False,
    duplicate_flag: bool = False,
) -> Dict[str, Any]:
    payload = {
        "submission_id": submission_id,
        "overall_status": overall_status,
        "fraud_flag": fraud_flag,
        "duplicate_flag": duplicate_flag,
        "stamp_valid": stamp_valid,
        "field_results": field_results,
    }
    response = get_supabase().table("validation_results").insert(payload).execute()
    return response.data[0]


def get_submission_with_document(submission_id: str) -> Dict[str, Any]:
    submission = (
        get_supabase().table("submissions").select("*").eq("id", submission_id).single().execute().data
    )
    document = (
        get_supabase()
        .table("documents")
        .select("*")
        .eq("submission_id", submission_id)
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return {"submission": submission, "document": document[0] if document else None}


def get_result_bundle(submission_id: str) -> Dict[str, Any]:
    validation = (
        get_supabase()
        .table("validation_results")
        .select("*")
        .eq("submission_id", submission_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    events = (
        get_supabase()
        .table("tool_call_events")
        .select("*")
        .eq("submission_id", submission_id)
        .order("executed_at")
        .execute()
        .data
    )
    status = get_supabase().table("submissions").select("status").eq("id", submission_id).single().execute().data
    return {
        "submission_id": submission_id,
        "status": status["status"],
        "validation_result": validation[0] if validation else None,
        "tool_call_events": events,
    }


def list_pending_submissions(older_than_seconds: int = 30) -> list[Dict[str, Any]]:
    query = (
        get_supabase()
        .table("submissions")
        .select("*")
        .eq("status", "pending")
        .lt("created_at", f"now()-interval '{older_than_seconds} seconds'")
    )
    return query.execute().data
