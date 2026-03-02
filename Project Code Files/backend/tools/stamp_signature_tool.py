import os
from io import BytesIO
from typing import Dict

import requests
from google.cloud import vision


def detect_stamp_signature(file_url: str) -> Dict[str, float | bool | str]:
    # Placeholder implementation for Phase 1.
    file_bytes = requests.get(file_url, timeout=30).content if file_url.startswith("http") else open(file_url, "rb").read()

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=file_bytes)
    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text.lower() if response.full_text_annotation else ""

    stamp_detected = "stamp" in text or "seal" in text
    signature_detected = "signature" in text or "sign" in text

    return {
        "stamp_detected": stamp_detected,
        "signature_detected": signature_detected,
        "confidence_score": 0.55 if (stamp_detected or signature_detected) else 0.35,
        "note": "Phase 1 placeholder using Google Vision text heuristics.",
    }
