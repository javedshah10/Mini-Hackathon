-- Phase 1 schema for Supabase PostgreSQL

create extension if not exists pgcrypto;

create table if not exists submissions (
  id uuid primary key default gen_random_uuid(),
  citizen_id uuid references citizens(id),
  employee_id uuid references employees(id),
  department_id uuid references departments(id),
  channel text default 'assisted',
  status text default 'pending',
  created_at timestamp default now()
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  submission_id uuid references submissions(id),
  file_name text,
  file_type text,
  file_url text,
  doc_type text,
  quality_score decimal(4,2),
  language text,
  uploaded_at timestamp default now()
);

create table if not exists tool_call_events (
  id uuid primary key default gen_random_uuid(),
  submission_id uuid references submissions(id),
  tool_name text,
  status text,
  confidence_score decimal(4,2),
  input_summary jsonb,
  output_summary jsonb,
  error_message text,
  executed_at timestamp default now()
);

create table if not exists validation_results (
  id uuid primary key default gen_random_uuid(),
  submission_id uuid references submissions(id),
  overall_status text,
  fraud_flag boolean default false,
  duplicate_flag boolean default false,
  stamp_valid boolean default false,
  field_results jsonb,
  created_at timestamp default now()
);
