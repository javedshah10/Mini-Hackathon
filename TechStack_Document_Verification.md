# Tech Stack Document
**AI-Powered Document Verification Platform**
Version 1.0 | March 2026 | Phase 1 Demo

---

## Overview

This document defines the complete technology stack for Phase 1 (Demo) and Production of the AI-Powered Document Verification Platform. The demo uses cloud services with synthetic data. Production uses on-premise deployment to meet data sovereignty requirements.

---

## Stack Summary

| Layer | Technology | Purpose | Environment |
|-------|-----------|---------|-------------|
| Frontend | Streamlit (Demo) / React (Production) | Operator/citizen-facing UI for upload, processing status, and results | Demo: Streamlit \| Production: React |
| Backend | FastAPI | REST API — handles file upload, pipeline trigger, result retrieval | Demo + Production |
| Storage | Supabase Storage | Stores uploaded document files — mirrors real-world server storage | Demo only |
| Database | Supabase PostgreSQL | Stores submissions, documents, tool call events, validation results | Demo only |
| OCR Engine | Tesseract OCR | Raw text and bounding box extraction from document images | Demo + Production |
| OCR Language Support | Hindi, Bengali, Telugu | Tesseract language packs: hin, ben, tel — Phase 1 scope | Demo + Production |
| Field Extraction | GPT OSS 20B via Groq | Parses raw OCR text into structured fields with confidence scores | Demo only |
| Agent Orchestration | GPT-4o (OpenAI) | Orchestrates all tool calls in sequence; manages pipeline logic | Demo only |
| Stamp & Signature Detection | Google Vision API | Phase 1 placeholder for stamp/seal/signature detection | Demo only |
| Production OCR | PaddleOCR + EasyOCR | Fine-tunable open-source OCR for regional language accuracy | Production |
| Production Field Extraction | Fine-tuned LayoutLM / Donut | Layout-aware field extraction for government document templates | Production |
| Production Stamp Detection | YOLOv8 + OpenCV | Fine-tuned object detection for government stamps and signatures | Production |

---

## 1. Frontend — Streamlit (Demo) / React (Production)

Streamlit is used for the Phase 1 demo — lightweight, Python-native, and ideal for rapid development. Production will use React for a scalable, maintainable, and government-grade user interface.

| Component | Detail |
|-----------|--------|
| Demo Framework | Streamlit |
| Production Framework | React |
| Language | Python (Demo) / JavaScript (Production) |
| UI Screens | Upload → Processing → Result |
| Upload Widget | Accepts PDF, JPEG, PNG — max 5MB |
| Language Selector | Dropdown: Hindi, Bengali, Telugu |
| Processing View | Step-by-step progress: OCR → Field Extraction → Classification → Validation → Stamp & Signature → Logging |
| Result View | Extracted fields table, confidence scores, overall status badge (PASSED / FAILED / ESCALATED), raw JSON toggle |
| Production Frontend | React — component-based architecture, multi-language UI, RBAC-aware views for operator, supervisor, and citizen roles |
| Deployment | Local for demo; Streamlit Cloud optional |

---

## 2. Backend — FastAPI

FastAPI provides the REST API layer between the frontend, Supabase, and the AI pipeline. High-performance, Python-native, and supports async operations.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /submit | POST | Accepts document upload, creates submission record, uploads file to Supabase Storage |
| /process/{id} | POST | Triggers GPT-4o agent pipeline for a given submission_id |
| /result/{id} | GET | Returns validation result and all tool call events for a submission |
| /health | GET | Health check endpoint |

---

## 3. Document Storage — Supabase Storage

Supabase Storage acts as the document file server for Phase 1. It mirrors the real-world architecture where documents are uploaded to an official portal and saved to a server before processing begins.

| Property | Detail |
|----------|--------|
| Bucket Name | documents |
| Supported Formats | PDF, JPEG, PNG |
| Max File Size | 5MB |
| Access | Signed URL generated per file — stored in documents.file_url |
| Real-World Equivalent | Government server where citizen portal uploads are saved before processing |
| Production Replacement | On-premise file server or NAS — no cloud storage in production (data sovereignty) |

---

## 4. Database — Supabase PostgreSQL

Supabase PostgreSQL stores all structured data. All 4 tables are linked via `submission_id`.

| Table | Purpose |
|-------|---------|
| submissions | Central record for every document submission — channel, status, timestamps |
| documents | File metadata — name, type, URL, doc_type, quality score, language |
| tool_call_events | Every AI Agent tool invocation logged — tool name, status, input/output, confidence score |
| validation_results | Final aggregated result per submission — overall status, fraud flag, field results |

---

## 5. OCR Engine — Tesseract

Tesseract OCR performs raw text extraction from uploaded document images. Open-source with Indian regional language script support via language packs.

| Property | Detail |
|----------|--------|
| Version | Tesseract 5.x |
| Supported Languages (Phase 1) | Hindi (hin), Bengali (ben), Telugu (tel) |
| Language Pack Installation | `sudo apt install tesseract-ocr-hin tesseract-ocr-ben tesseract-ocr-tel` |
| Unsupported Language Handling | Return error: `Language not supported in Phase 1. Supported: Hindi, Bengali, Telugu.` |
| Output | Raw extracted text, bounding boxes, character confidence scores |
| Production Replacement | PaddleOCR (primary) + EasyOCR (secondary) — fine-tuned for regional scripts |

---

## 6. Field Extraction — GPT OSS 20B via Groq

Groq hosts the GPT OSS 20B model for high-speed field extraction. It receives raw OCR text and returns structured fields as JSON with confidence scores.

| Property | Detail |
|----------|--------|
| Provider | Groq API |
| Model | GPT OSS 20B (llama3-groq-70b-8192-tool-use-preview or equivalent) |
| Input | Raw OCR text from Tesseract |
| Output | Structured JSON — full_name, date_of_birth, id_number, address, reference_number, confidence_score |
| Prompt Strategy | Zero-shot JSON extraction — returns JSON only, no explanation |
| Fallback | If confidence_score < 0.6, submission status set to `escalated` |
| Production Replacement | Fine-tuned LayoutLM or Donut — layout-aware field extraction on-premise |

---

## 7. Agent Orchestration — GPT-4o

GPT-4o acts as the AI Agent orchestrator. It sequences all tool calls, handles errors, applies channel-specific logic, and ensures every step is logged to the database.

| Property | Detail |
|----------|--------|
| Provider | OpenAI API |
| Model | gpt-4o |
| Role | AI Agent orchestrator — sequences and manages all tool calls |
| Tools Called in Order | ocr_tool → field_extractor_tool → classifier_tool → field_validator_tool → stamp_signature_tool → audit_logger_tool |
| Error Handling | On any tool failure → log error, set submission status = `failed`, stop pipeline |
| Escalation Logic | If confidence_score < 0.6 → set submission status = `escalated` |
| Production Replacement | LangGraph or custom state machine — lightweight on-premise agent framework |

---

## 8. Stamp & Signature Detection — Google Vision API (Placeholder)

Google Vision API is used as a Phase 1 placeholder. It does not natively detect government stamps or signatures — demo stand-in only. Production will use fine-tuned YOLOv8 + OpenCV.

| Property | Detail |
|----------|--------|
| Provider | Google Cloud Vision API |
| Usage in Phase 1 | Placeholder demo — document_text_detection or object_localization on document image |
| Limitation | Does not natively detect government stamps or signatures accurately |
| Output | stamp_detected: true/false, signature_detected: true/false, confidence_score |
| Phase 1 Note | Result logged to tool_call_events with placeholder flag in output_summary |
| Production Replacement | Fine-tuned YOLOv8 + OpenCV — trained on annotated government stamp/signature bounding boxes |

---

## 9. Demo vs Production Comparison

| Component | Phase 1 Demo | Production |
|-----------|-------------|-----------|
| Frontend | Streamlit | React |
| Backend | FastAPI | FastAPI |
| Storage | Supabase Storage | On-premise file server |
| Database | Supabase PostgreSQL | On-premise PostgreSQL |
| OCR | Tesseract OCR | PaddleOCR + EasyOCR (fine-tuned) |
| Field Extraction | GPT OSS 20B via Groq | Fine-tuned LayoutLM / Donut |
| Agent Orchestration | GPT-4o (OpenAI) | LangGraph or custom state machine |
| Stamp Detection | Google Vision API (placeholder) | YOLOv8 + OpenCV (fine-tuned) |
| Fraud Detection | Out of scope (Phase 1) | ML anomaly detection + rule-based heuristics |
| Data | Synthetic / test documents only | Anonymized real documents (data governance approved) |
| Authentication | None (Phase 1) | RBAC — operator, supervisor, citizen, it_admin |
| Offline Mode | Not supported (Phase 1) | Full offline with sync on connectivity restore |

---

## 10. Environment Variables

| Variable | Purpose |
|----------|---------|
| SUPABASE_URL | Supabase project URL |
| SUPABASE_KEY | Supabase service role key |
| SUPABASE_BUCKET | Storage bucket name — set to: `documents` |
| OPENAI_API_KEY | OpenAI API key for GPT-4o agent orchestration |
| GROQ_API_KEY | Groq API key for GPT OSS 20B field extraction |
| GOOGLE_VISION_API_KEY | Google Cloud Vision API key for stamp/signature placeholder |

---

*Version 1.0 | Status: Draft for Review*
