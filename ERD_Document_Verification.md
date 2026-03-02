# Entity Relationship Document
**AI-Powered Document Verification Platform**
Version 1.0 | March 2026 | Draft for Review

---

## Overview

This ERD defines 8 core database entities. The design is intentionally simple — every AI Agent tool call is stored as a discrete event for full audit traceability. All entities link back to the central `submissions` table.

---

## 1. departments

Stores the government departments that use or integrate with the platform.

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique department identifier |
| name | VARCHAR(150) | | Full department name |
| created_at | TIMESTAMP | | Record creation timestamp |

---

## 2. citizens

Stores citizens who submit documents via the online self-service channel. Grows independently from employee records.

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique citizen identifier |
| name | VARCHAR(100) | | Full name |
| national_id | VARCHAR(50) | | National ID number (e.g. Aadhaar) |
| phone | VARCHAR(20) | | Mobile number for OTP verification |
| email | VARCHAR(150) | | Email address for notifications |
| city | VARCHAR(100) | | City of residence |
| created_at | TIMESTAMP | | Record creation timestamp |

---

## 3. employees

Stores government service center staff — operators, supervisors, and IT admins. Linked to a department.

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique employee identifier |
| name | VARCHAR(100) | | Full name |
| email | VARCHAR(150) | | Work email address |
| role | ENUM | | operator \| supervisor \| it_admin |
| department_id | UUID | FK | References departments.id |
| created_at | TIMESTAMP | | Record creation timestamp |

---

## 4. submissions ⭐

The central entity. Every document submission from either channel creates one record here. All other entities link back to this table.

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique submission identifier |
| citizen_id | UUID | FK | References citizens.id (online channel; null for assisted) |
| employee_id | UUID | FK | References employees.id (assisted channel; null for online) |
| department_id | UUID | FK | References departments.id |
| channel | ENUM | | assisted \| online |
| status | ENUM | | pending \| processing \| passed \| failed \| escalated |
| created_at | TIMESTAMP | | Submission timestamp |

---

## 5. documents

Stores metadata for each uploaded document. One submission can have multiple documents (e.g. Aadhaar + income certificate).

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique document identifier |
| submission_id | UUID | FK | References submissions.id |
| file_name | VARCHAR(255) | | Original uploaded file name (e.g. aadhaar_scan.pdf) |
| file_type | VARCHAR(10) | | File format — pdf \| jpeg \| png |
| doc_type | VARCHAR(100) | | AI-classified document type (e.g. Aadhaar Card) |
| quality_score | DECIMAL(4,2) | | Image quality score (0–1.0) |
| language | VARCHAR(50) | | Detected document language/script |
| uploaded_at | TIMESTAMP | | File upload timestamp |

---

## 6. tool_call_events

Logs every AI Agent tool invocation. Each row = one tool call for one submission. This is the core traceability table — every agent action is recorded here.

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique event identifier |
| submission_id | UUID | FK | References submissions.id |
| tool_name | VARCHAR(50) | | See ENUM reference below |
| status | ENUM | | success \| failed \| skipped |
| confidence_score | DECIMAL(4,2) | | Output confidence score (0–1.0) |
| input_summary | JSONB | | Key inputs passed to the tool |
| output_summary | JSONB | | Key outputs returned by the tool |
| error_message | TEXT | | Error details if tool call failed |
| executed_at | TIMESTAMP | | Tool execution timestamp |

---

## 7. validation_results

Stores the final aggregated validation outcome per submission. One record per submission (1:1 with submissions).

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique result identifier |
| submission_id | UUID | FK | References submissions.id (1:1) |
| overall_status | ENUM | | passed \| failed \| escalated \| pending_review |
| fraud_flag | BOOLEAN | | True if fraud or tamper detected |
| duplicate_flag | BOOLEAN | | True if duplicate submission detected |
| stamp_valid | BOOLEAN | | True if required stamps/signatures found |
| field_results | JSONB | | Per-field extraction and validation details |
| created_at | TIMESTAMP | | Result generation timestamp |

---

## 8. audit_logs

Records every human action taken on a submission. Separate from tool_call_events — this captures operator and supervisor decisions, not AI Agent actions.

| Field | Data Type | Key | Description |
|-------|-----------|-----|-------------|
| id | UUID | PK | Unique log entry identifier |
| submission_id | UUID | FK | References submissions.id |
| employee_id | UUID | FK | References employees.id (who took the action) |
| action | VARCHAR(100) | | approved \| rejected \| escalated \| overridden \| correction_submitted |
| notes | TEXT | | Operator/supervisor notes or correction details |
| created_at | TIMESTAMP | | Action timestamp |

---

## Relationships Summary

| From | To | Cardinality | Description |
|------|----|-------------|-------------|
| departments | employees | 1 : Many | A department has many employees |
| departments | submissions | 1 : Many | A department receives many submissions |
| citizens | submissions | 1 : Many | A citizen makes many online submissions |
| employees | submissions | 1 : Many | An employee processes many assisted submissions |
| submissions | documents | 1 : Many | A submission can have multiple uploaded documents |
| submissions | tool_call_events | 1 : Many | Each submission triggers multiple agent tool calls |
| submissions | validation_results | 1 : 1 | Each submission has exactly one final result |
| submissions | audit_logs | 1 : Many | A submission can have multiple operator actions logged |
| employees | audit_logs | 1 : Many | An employee can perform many audit actions across submissions |

---

## ENUM Reference

**employees.role**
- `operator` — Service center staff processing documents
- `supervisor` — Reviews flagged documents; makes final decisions
- `it_admin` — Department IT team managing API integration

**submissions.channel**
- `assisted` — Document submitted by operator at a service center
- `online` — Document submitted by citizen via self-service portal

**submissions.status**
- `pending` — Submitted, not yet processed
- `processing` — AI Agent pipeline currently running
- `passed` — All validations passed
- `failed` — One or more validations failed
- `escalated` — Flagged for supervisor review

**tool_call_events.tool_name**
- `ocr_tool` — Raw text extraction from document image
- `field_extractor_tool` — LLM/LayoutLM parses raw text into structured fields
- `classifier_tool` — Document type identification
- `field_validator_tool` — Field format and rule validation
- `stamp_signature_tool` — Stamp and signature presence detection
- `fraud_tamper_tool` — Fraud and tamper detection
- `audit_logger_tool` — Database event logging
- `sync_manager_tool` — Offline queue management and sync
- `notification_tool` — Citizen/operator status notifications

---

## Design Notes

- `citizens` and `employees` are separate tables — citizens grow independently as online submissions scale; employees remain a small, stable dataset.
- `submissions.citizen_id` is null for assisted channel; `submissions.employee_id` is null for online channel.
- All primary keys use UUID to support distributed deployment across departments.
- JSONB fields store flexible AI output without schema changes as tools evolve.
- `tool_call_events` = AI Agent actions. `audit_logs` = Human actions. Kept separate intentionally.
- `submissions` is the central hub — full processing history for any submission can be reconstructed from this table.
- `validation_results` is 1:1 with submissions — the final aggregated output after all tool calls complete.
- Recommended database: PostgreSQL (native JSONB and UUID support).

---

*Document prepared by: AI Product Manager | Version: 1.0 | Status: Draft for Review*
