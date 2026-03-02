import re
from typing import Any, Dict


DOB_REGEX = re.compile(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}$")
ALNUM_REGEX = re.compile(r"^[A-Za-z0-9]+$")


def validate_fields(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    confidence = float(extracted_fields.get("confidence_score") or 0)

    full_name = extracted_fields.get("full_name")
    dob = extracted_fields.get("date_of_birth")
    id_number = extracted_fields.get("id_number")

    field_results = {
        "full_name": {
            "value": full_name,
            "status": "pass" if isinstance(full_name, str) and len(full_name.strip()) >= 2 else "fail",
        },
        "date_of_birth": {
            "value": dob,
            "status": "pass" if isinstance(dob, str) and DOB_REGEX.match(dob) else "fail",
        },
        "id_number": {
            "value": id_number,
            "status": "pass" if isinstance(id_number, str) and ALNUM_REGEX.match(id_number) else "fail",
        },
        "confidence_score": {
            "value": confidence,
            "status": "pass" if confidence >= 0.6 else "review",
        },
    }

    fail_exists = any(v["status"] == "fail" for v in field_results.values())
    overall_status = "failed" if fail_exists else "passed"

    return {"overall_status": overall_status, "field_results": field_results}
