import re
from dataclasses import dataclass
from io import BytesIO
from typing import Iterator

import pdfplumber
import pytesseract
import requests
from pdf2image import convert_from_bytes
from PIL import Image


SUPPORTED_LANGUAGES = {"hin": "Hindi", "ben": "Bengali", "tel": "Telugu"}
PDF_CHUNK_SIZE = 5


@dataclass
class OCRResult:
    raw_text: str
    detected_language: str
    confidence_score: float


def _ocr_text_and_confidence(image: Image.Image, lang: str) -> tuple[str, float]:
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)

    words: list[str] = []
    conf_values: list[float] = []

    for text, conf in zip(data.get("text", []), data.get("conf", [])):
        token = (text or "").strip()
        if token:
            words.append(token)

        conf_raw = str(conf).strip()
        if conf_raw and conf_raw != "-1":
            conf_values.append(float(conf_raw))

    text_output = " ".join(words).strip()
    avg_conf = round(sum(conf_values) / (len(conf_values) * 100), 2) if conf_values else 0.0
    return text_output, avg_conf


def _iter_pdf_images(file_bytes: bytes, total_pages: int, chunk_size: int = PDF_CHUNK_SIZE) -> Iterator[Image.Image]:
    for start in range(1, total_pages + 1, chunk_size):
        end = min(start + chunk_size - 1, total_pages)
        images = convert_from_bytes(file_bytes, first_page=start, last_page=end)
        for image in images:
            try:
                yield image
            finally:
                image.close()


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
            total_pages = len(pdf.pages)

        if digital_text and len(re.sub(r"\s+", "", digital_text)) > 20:
            return OCRResult(raw_text=digital_text, detected_language=language, confidence_score=0.95)

        page_text: list[str] = []
        confidences: list[float] = []
        for image in _iter_pdf_images(file_bytes, total_pages=total_pages):
            text, conf = _ocr_text_and_confidence(image, language)
            page_text.append(text)
            confidences.append(conf)

        conf = round(sum(confidences) / max(len(confidences), 1), 2)
        return OCRResult(raw_text="\n".join(page_text).strip(), detected_language=language, confidence_score=conf)

    with Image.open(BytesIO(file_bytes)) as image:
        text, conf = _ocr_text_and_confidence(image, language)
    return OCRResult(raw_text=text, detected_language=language, confidence_score=conf)
