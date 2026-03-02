import json
import os
from typing import Any, Dict

from openai import OpenAI


def classify_document(raw_text: str, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = (
        "Classify the Indian government document type based on OCR text and extracted fields. "
        "Return JSON with keys: doc_type (string), confidence_score (float 0-1)."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You classify documents."},
            {
                "role": "user",
                "content": f"{prompt}\nOCR:\n{raw_text}\n\nFields:\n{json.dumps(extracted_fields)}",
            },
        ],
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)
