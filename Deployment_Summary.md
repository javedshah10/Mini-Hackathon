# Deployment Plan — Summary
**AI-Powered Document Verification Platform**
Version 1.0 | March 2026 | Draft

---

## Phase 1 — Demo Deployment

| Item | Detail |
|------|--------|
| Objective | Validate end-to-end pipeline with synthetic documents. No real citizen PII. |
| Target Date | Week 2 from project kick-off |
| Environment | Cloud — all services hosted externally |
| Data | Synthetic documents generated via Faker + document templates |
| Access | Internal team only — no public access |

### Demo Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Streamlit | Simple UI — upload, processing status, results |
| Backend | FastAPI | REST API — submit, process, retrieve results |
| Storage | Supabase Storage | Document file bucket — mirrors real server upload flow |
| Database | Supabase PostgreSQL | All structured data — submissions, tool events, results |
| OCR | Tesseract OCR | Hindi, Bengali, Telugu only in Phase 1 |
| Field Extraction | GPT OSS 20B via Groq | Raw OCR text → structured fields + confidence scores |
| Agent Orchestration | GPT-4o (OpenAI) | Sequences all tool calls; logs every event |
| Stamp Detection | Google Vision API | Placeholder only — not production-accurate |

### Demo Readiness Checklist

- ✅ Document uploads to Supabase Storage
- ✅ Tesseract extracts text in Hindi, Bengali, and Telugu
- ✅ Groq returns structured fields as valid JSON
- ✅ GPT-4o orchestrates full tool sequence
- ✅ Every tool call logged to `tool_call_events`
- ✅ Streamlit displays result in under 30 seconds

---

## Phase 2 — Production Deployment

| Item | Detail |
|------|--------|
| Objective | Full production rollout — on-premise, real citizen documents, RBAC enforced |
| Target Date | Week 8 onwards — after KPI validation from demo phase |
| Environment | On-premise — all services hosted on government infrastructure |
| Data | Anonymized real documents from pilot departments (data governance approved) |
| Access | Role-based — operator, supervisor, citizen, it_admin |

### Production Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React | RBAC-aware views per user role |
| Backend | FastAPI | Same API layer — production-hardened |
| Storage | On-premise file server | No cloud storage — data sovereignty requirement |
| Database | On-premise PostgreSQL | Full schema — citizens, employees, all 8 tables |
| OCR | PaddleOCR + EasyOCR | Fine-tuned for regional scripts — target CER <5% |
| Field Extraction | Fine-tuned LayoutLM / Donut | Layout-aware — trained on government templates |
| Agent Orchestration | LangGraph / custom state machine | Lightweight on-premise agent framework |
| Stamp Detection | YOLOv8 + OpenCV | Fine-tuned on annotated bounding box dataset |
| Fraud Detection | ML anomaly + rule-based | Hybrid — reduces false positives |

### Rollout Milestones

| Milestone | Target Week | Status |
|-----------|-------------|--------|
| Demo environment ready (cloud, synthetic data) | Week 2 | Planned |
| Operator UAT at pilot service center | Week 3–4 | Planned |
| OCR fine-tuning round 1 (regional languages) | Week 4–6 | Planned |
| First department API integration | Week 5–7 | Planned |
| Production deployment — shadow mode (pilot center) | Week 8 | Planned |
| KPI baseline measurement | Week 8–9 | Planned |
| Assisted channel full launch | Week 10 | Planned |
| Online (citizen) channel UAT | Week 10–11 | Planned |
| KPI review — decision on broader rollout | Week 12 | Planned |

### Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| OCR accuracy low for regional scripts | Fine-tune PaddleOCR; route low-confidence to human review |
| Fraud detection false positives | Hybrid ML + rules; supervisor review queue for flagged cases |
| Data sovereignty breach | Zero cloud transmission in production; on-premise only |
| Citizen portal misuse | Stricter automated guardrails; re-upload prompts; no raw fraud flags exposed |

---

*Version 1.0 | Draft for Review*
