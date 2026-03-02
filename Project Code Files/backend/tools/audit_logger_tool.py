from typing import Any, Dict

from db import upsert_validation_result, update_submission_status


def write_final_result(
    submission_id: str,
    overall_status: str,
    field_results: Dict[str, Any],
    stamp_valid: bool,
) -> Dict[str, Any]:
    validation_record = upsert_validation_result(
        submission_id=submission_id,
        overall_status=overall_status,
        field_results=field_results,
        stamp_valid=stamp_valid,
    )
    update_submission_status(submission_id, overall_status)
    return {"validation_result": validation_record, "submission_status": overall_status}
