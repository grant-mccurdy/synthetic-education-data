# Supabase/Postgres Deployment Scaffold

## Purpose

This document describes the optional hosted SQL serving path for the synthetic education warehouse.

The project keeps DuckDB as the canonical local warehouse because it is free, reproducible, file-based, and easy to rebuild from the public synthetic artifacts. Supabase/Postgres is useful as a hosted serving layer when remote SQL queries, API-style access, or a more production-like database target are useful.

## Architecture

```text
synthetic CSV and Canvas-style JSON artifacts
-> DuckDB raw and raw_canvas schemas
-> DuckDB mart schema and validation checks
-> exported public-safe CSV marts
-> Supabase/Postgres lms and analytics schemas
-> selected public read-only views
-> downstream assessment-intelligence extracts
```

The hosted warehouse publishes synthetic LMS staging tables:

- `lms.canvas_courses`
- `lms.canvas_sections`
- `lms.canvas_enrollments`

and validated analytics tables:

- `analytics.dim_student`
- `analytics.dim_course`
- `analytics.dim_teacher`
- `analytics.dim_section`
- `analytics.dim_assignment`
- `analytics.student_readiness`
- `analytics.fact_assessment_score`
- `analytics.fact_lms_enrollment`
- `analytics.validation_summary`
- `analytics.pipeline_runs`

Base `lms` and `analytics` tables remain outside the public API contract. Downstream projects should use these public views:

- `public.course_section_performance`
- `public.assignment_growth_by_course`
- `public.nonparticipation_by_group`
- `public.lms_enrollment_reconciliation`
- `public.student_readiness_extract`
- `public.warehouse_summary`
- `public.warehouse_validation_summary`

## Local Setup

Build the local synthetic artifacts and DuckDB warehouse first:

```bash
make all
make analytics-install
make warehouse
```

Install the optional Postgres dependency:

```bash
make postgres-install
```

Validate the publishable files without connecting to Supabase:

```bash
make supabase-load-dry-run
```

The dry run checks that the expected mart CSVs exist, match the Postgres schema columns, and have readable row counts.

## Supabase Connection

Use environment variables or an untracked local `.env` file for secrets. The loader supports two connection paths:

```text
SUPABASE_ACCESS_TOKEN=
SUPABASE_DATABASE_URL=
```

If `SUPABASE_DATABASE_URL` is set, the loader uses direct Postgres. Otherwise it uses `SUPABASE_ACCESS_TOKEN` and the Supabase Management API. Do not commit `.env`, passwords, service-role keys, API keys, or private LMS credentials.

To load the hosted database:

```bash
make supabase-load
```

The loader runs:

```text
sql/postgres/00_analytics_schema.sql
```

then loads synthetic LMS staging rows, curated analytics marts, run metadata, validation summaries, and public read-only views.

Validate the hosted warehouse after loading:

```bash
make supabase-validate
```

## Why DuckDB Still Matters

DuckDB and Supabase/Postgres serve different roles:

- DuckDB is the reproducible build, validation, and local analytics warehouse.
- Supabase/Postgres is the optional hosted serving layer.

This mirrors a common analytics pattern: local or batch transformation produces curated tables, then a hosted relational database serves those tables to applications, dashboards, or API clients.

## Current Boundary

This scaffold does not publish real student data, real Canvas exports, private assessment records, or credentials. It publishes synthetic, validated, public-safe analytics marts only.

Optional OpenAI validation narrative:

```bash
make supabase-validation-narrative
```

This default target is local only. It writes a prompt preview and deterministic narrative from aggregate validation metadata. Passing `--call-api` to the script sends only aggregate row counts and validation statuses to OpenAI.
