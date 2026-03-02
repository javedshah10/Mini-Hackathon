import os
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Dict

import pdfplumber
import pytesseract
import requests
from pdf2image import convert_from_bytes
from PIL import Image


SUPPORTED_LANGUAGES = {"hin": "Hindi", "ben": "Bengali", "tel": "Telugu"}


@dataclass
class OCRResult:
    raw_text: str
    detected_language: str
    confidence_score: float


def _avg_confidence(image: Image.Image, lang: str) -> float:
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    conf = [float(c) for c in data.get("conf", []) if c not in ("-1", -1)]
    if not conf:
        return 0.0
    return round(sum(conf) / (len(conf) * 100), 2)


def _download_file(file_url: str) -> bytes:
    if file_url.startswith("http"):
        return requests.get(file_url, timeout=30).content
    with open(file_url, "rb") as f:
        return f.read()


def run_ocr(file_url: str, language: str) -> OCRResult:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("Language not supported in Phase 1. Supported: Hindi, Bengali, Telugu.")

    file_bytes = _download_file(file_url)
    is_pdf = file_url.lower().endswith(".pdf")

    if is_pdf:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            digital_text = "\n".join((p.extract_text() or "") for p in pdf.pages).strip()
        if digital_text and len(re.sub(r"\s+", "", digital_text)) > 20:
            return OCRResult(raw_text=digital_text, detected_language=language, confidence_score=0.95)

        images = convert_from_bytes(file_bytes)
        page_text = []
        confidences = []
        for image in images:
            page_text.append(pytesseract.image_to_string(image, lang=language))
            confidences.append(_avg_confidence(image, language))
        conf = round(sum(confidences) / max(len(confidences), 1), 2)
        return OCRResult(raw_text="\n".join(page_text).strip(), detected_language=language, confidence_score=conf)

    image = Image.open(BytesIO(file_bytes))
    text = pytesseract.image_to_string(image, lang=language)
    conf = _avg_confidence(image, language)
    return OCRResult(raw_text=text.strip(), detected_language=language, confidence_score=conf)
