import json
import os
from typing import Any, Dict

from groq import Groq


DEFAULT_GROQ_MODEL = "llama3-groq-70b-8192-tool-use-preview"
MODEL_NAME = os.getenv("GROQ_MODEL_NAME", DEFAULT_GROQ_MODEL)


def extract_fields(raw_text: str) -> Dict[str, Any]:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""You are a document field extraction assistant for Indian government documents.
Extract the following fields from the raw OCR text below.
Return ONLY a valid JSON object with these keys:
- full_name (string)
- date_of_birth (string, format DD/MM/YYYY)
- id_number (string)
- address (string)
- reference_number (string)
- confidence_score (float, 0.0 to 1.0, your overall confidence in the extraction)

If a field is not found, set its value to null.
Do not include any explanation. Return JSON only.

Raw OCR Text:
{raw_text}
"""
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = completion.choices[0].message.content.strip()
    return json.loads(content)
