# DuckDB Analytics Warehouse

This project includes an optional DuckDB analytics layer that turns the generated synthetic math department artifacts into SQL-queryable raw tables and dashboard-ready marts.

The intent is to model a modern education analytics workflow:

```text
synthetic LMS / assessment artifacts
-> local DuckDB warehouse
-> SQL validation and mart queries
-> public-safe reporting extracts
-> downstream dashboarding in assessment-intelligence
```

The warehouse also simulates a practical LMS-to-SQL extraction pattern. The generated Canvas-style course JSON profiles function as public-safe API-like payloads. The build script normalizes those profiles into relational `raw_canvas` tables, then reconciles the SQL extract against the canonical synthetic enrollment model.

The final reporting layer includes a small star schema for downstream assessment analytics:

```text
dim_student
dim_course
dim_section
dim_teacher
dim_assignment
fact_assessment_score
fact_lms_enrollment
```

## Why DuckDB

DuckDB is a free embedded analytical database. It works well for a local analytics warehouse because it supports SQL, Python, CSV/Parquet-style workflows, reproducibility, and single-file database storage without a hosted service.

The generated database file is local-only:

```text
warehouse/synthetic_math.duckdb
```

The public-safe mart exports are written to:

```text
data/marts/
```

## Install Optional Analytics Dependency

```bash
make analytics-install
```

## Build The Warehouse

```bash
make warehouse
```

This target:

1. creates `raw` and `mart` schemas in DuckDB
2. loads the public-safe synthetic CSV and JSON artifacts
3. runs SQL models from `sql/marts/`
4. exports mart CSVs to `data/marts/`
5. checks `mart.validation_summary`

## SQL Models

Raw schema:

- `raw.gradebook`
- `raw.students`
- `raw.school_years`
- `raw.teachers`
- `raw.courses`
- `raw.sections`
- `raw.enrollments`
- `raw.assignments`
- `raw.assessment_scores`
- `raw_canvas.courses`
- `raw_canvas.sections`
- `raw_canvas.enrollments`

Mart schema:

- `mart.student_assessment_long`
- `mart.canvas_roster_sql_extract`
- `mart.student_readiness`
- `mart.dim_student`
- `mart.dim_course`
- `mart.dim_teacher`
- `mart.dim_section`
- `mart.dim_assignment`
- `mart.fact_assessment_score`
- `mart.assignment_growth`
- `mart.course_section_summary`
- `mart.missingness_attendance`
- `mart.teacher_section_effects`
- `mart.lms_to_sql_roster_reconciliation`
- `mart.canvas_course_pipeline_audit`
- `mart.fact_lms_enrollment`
- `mart.validation_summary`

## Star Schema

The star schema is designed for dashboard and reporting tools that expect facts joined to stable dimensions.

```text
fact_assessment_score
  -> dim_student
  -> dim_course
  -> dim_section
  -> dim_teacher
  -> dim_assignment

fact_lms_enrollment
  -> dim_student
  -> dim_course
  -> dim_section
  -> dim_teacher
```

`fact_assessment_score` stores one row per active synthetic student assessment window. The warehouse is loaded from `data/synthetic/synthetic_assessment_scores_long.csv`, which is the preferred multi-year reporting source. It includes observed score fields, attendance/non-participation fields, observed posterior readiness, and hidden latent-readiness transition fields for method inspection.

`fact_lms_enrollment` stores one row per active synthetic student-year Canvas-derived enrollment and includes reconciliation status from the LMS-to-SQL roster check.

## Canvas-To-SQL Simulation

The Canvas profile extraction path is intentionally explicit:

```text
data/synthetic/canvas_course_profiles/<school_year>/*.json
-> raw_canvas.courses
-> raw_canvas.sections
-> raw_canvas.enrollments
-> mart.canvas_roster_sql_extract
-> mart.lms_to_sql_roster_reconciliation
-> mart.canvas_course_pipeline_audit
```

This mirrors a school-side workflow where LMS API payloads are extracted, normalized into SQL tables, and reconciled before being used for reporting. The public version uses only synthetic Canvas-style profiles.

## Downstream Use

The exported mart CSVs are intended to become the input layer for `assessment-intelligence`.

Recommended handoff pattern:

```text
synthetic-education-data/data/marts/*.csv
-> assessment-intelligence/data/external/synthetic-education-data/
-> dashboard/reporting pipeline
```

Recommended first downstream queries:

- course and section score distributions from `fact_assessment_score`
- assignment growth by course, section, and teacher
- non-participation rates by grade, course, and attendance category
- enrollment counts and reconciliation status from `fact_lms_enrollment`

See [star-schema-erd.md](star-schema-erd.md) for the fact/dimension diagram.

Readable SQL examples live in:

```text
sql/examples/
```

This keeps the synthetic data engine focused on generation, validation, SQL modeling, and public-safe exports while leaving visual analytics and interpretation to the downstream assessment project.

## Hosted Postgres/Supabase Layer

The implemented warehouse is local and reproducible through DuckDB. The repo also includes a scaffold for publishing validated star-schema marts to hosted Postgres, such as Supabase.

The intended architecture is:

```text
synthetic Canvas/LMS artifacts
-> local DuckDB warehouse
-> validated star-schema marts
-> optional Supabase/Postgres load
-> API-accessible synthetic analytics tables
```

DuckDB remains the canonical local build and validation layer. Supabase/Postgres is the optional hosted serving layer for public-safe synthetic tables, remote SQL querying, and API-style access after a private connection string is configured.

Implemented scaffold items:

- `.env.example` with `SUPABASE_DATABASE_URL`
- Postgres DDL for the `analytics` schema
- loader script that publishes validated DuckDB star-schema mart exports into Postgres
- documentation for Supabase setup without committing credentials

Current boundary:

- DuckDB continues to own raw synthetic CSV/JSON loading, Canvas JSON normalization, validation, and mart generation.
- Supabase/Postgres publishes the validated analytics facts and dimensions as a hosted serving layer.
- Raw Canvas and raw assessment schemas can be added later if the hosted serving layer needs raw-layer inspection.
- `assessment-intelligence` still uses the local DuckDB extract path by default; hosted Postgres query mode can be added after a Supabase project is configured.

Use:

```bash
make postgres-load-dry-run
```

to validate publishable CSV headers and row counts without opening a database connection.

Do not commit real Supabase credentials, connection strings, service-role keys, real Canvas exports, or private institutional data.
