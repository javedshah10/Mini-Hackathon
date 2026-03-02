from typing import Any, Dict

from db import get_submission_with_document, log_tool_event, update_submission_status
from tools.audit_logger_tool import write_final_result
from tools.classifier_tool import classify_document
from tools.field_extractor_tool import extract_fields
from tools.field_validator_tool import validate_fields
from tools.ocr_tool import run_ocr
from tools.stamp_signature_tool import detect_stamp_signature


def _log_skipped(submission_id: str, tool_name: str, reason: str) -> None:
    log_tool_event(
        submission_id=submission_id,
        tool_name=tool_name,
        status="skipped",
        output_summary={"reason": reason},
    )


def run_submission_pipeline(submission_id: str) -> Dict[str, Any]:
    bundle = get_submission_with_document(submission_id)
    document = bundle["document"]
    if not document:
        raise ValueError("No document found for submission")

    if bundle["submission"]["status"] not in {"pending", "processing"}:
        return {"status": "skipped", "reason": "submission already finalized"}

    try:
        update_submission_status(submission_id, "processing")

        ocr_result = run_ocr(document["file_url"], document["language"])
        log_tool_event(
            submission_id,
            "ocr_tool",
            "success",
            confidence_score=ocr_result.confidence_score,
            input_summary={"file_url": document["file_url"], "language": document["language"]},
            output_summary={
                "detected_language": ocr_result.detected_language,
                "raw_text_preview": ocr_result.raw_text[:500],
            },
        )

        fields = extract_fields(ocr_result.raw_text)
        log_tool_event(
            submission_id,
            "field_extractor_tool",
            "success",
            confidence_score=float(fields.get("confidence_score") or 0),
            input_summary={"raw_text_preview": ocr_result.raw_text[:500]},
            output_summary=fields,
        )

        classification = classify_document(ocr_result.raw_text, fields)
        log_tool_event(
            submission_id,
            "classifier_tool",
            "success",
            confidence_score=float(classification.get("confidence_score") or 0),
            input_summary={"fields": fields},
            output_summary=classification,
        )

        validation = validate_fields(fields)
        log_tool_event(
            submission_id,
            "field_validator_tool",
            "success",
            input_summary={"fields": fields},
            output_summary=validation,
        )

        stamp_info = detect_stamp_signature(document["file_url"])
        log_tool_event(
            submission_id,
            "stamp_signature_tool",
            "success",
            confidence_score=float(stamp_info.get("confidence_score") or 0),
            input_summary={"file_url": document["file_url"]},
            output_summary=stamp_info,
        )

        overall_status = validation["overall_status"]
        if float(fields.get("confidence_score") or 0) < 0.6:
            overall_status = "escalated"

        final_result = write_final_result(
            submission_id=submission_id,
            overall_status=overall_status,
            field_results={
                **validation["field_results"],
                "classification": classification,
                "stamp_signature": stamp_info,
            },
            stamp_valid=bool(stamp_info.get("stamp_detected") or stamp_info.get("signature_detected")),
        )

        log_tool_event(
            submission_id,
            "audit_logger_tool",
            "success",
            output_summary=final_result,
        )

        _log_skipped(submission_id, "notification_tool", "Phase 1 — Streamlit UI handles display")
        _log_skipped(submission_id, "sync_manager_tool", "Phase 1 — offline mode not supported")
        _log_skipped(submission_id, "fraud_tamper_tool", "Phase 1 — out of scope")

        return {"status": overall_status, "result": final_result}
    except Exception as exc:
        update_submission_status(submission_id, "failed")
        log_tool_event(
            submission_id,
            "pipeline",
            "failed",
            error_message=str(exc),
            output_summary={"step": "exception"},
        )
        raise
