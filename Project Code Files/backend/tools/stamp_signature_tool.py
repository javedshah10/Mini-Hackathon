from typing import Dict

import requests
from google.cloud import vision


STAMP_KEYWORDS = {"stamp", "seal", "emblem"}
SIGNATURE_KEYWORDS = {"signature", "autograph", "sign"}


def _download_document(file_url: str) -> bytes:
    if file_url.startswith("http"):
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        return response.content
    with open(file_url, "rb") as file:
        return file.read()


def detect_stamp_signature(file_url: str) -> Dict[str, float | bool | str]:
    """Phase 1 placeholder implementation using Google Vision object localization."""
    file_bytes = _download_document(file_url)

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=file_bytes)
    response = client.object_localization(image=image)

    objects = response.localized_object_annotations or []
    labels = {obj.name.lower() for obj in objects}

    stamp_detected = any(any(key in label for key in STAMP_KEYWORDS) for label in labels)
    signature_detected = any(any(key in label for key in SIGNATURE_KEYWORDS) for label in labels)
    confidence_score = round(max((obj.score for obj in objects), default=0.0), 2)

    return {
        "stamp_detected": stamp_detected,
        "signature_detected": signature_detected,
        "confidence_score": confidence_score,
        "note": "Phase 1 placeholder — Google Vision API. Production will use YOLOv8 + OpenCV.",
    }
