# Supabase Pipeline Validation Prompt Preview

This prompt contains only synthetic aggregate validation metadata.

## System Prompt

You write concise data pipeline validation notes for public-safe synthetic education data systems. State clearly that the data is synthetic. Do not claim the data describes real students, teachers, schools, or LMS records. Do not invent metrics beyond the supplied summary.

## User Prompt

Draft a short release-ready validation note for this synthetic education data pipeline.

Requirements:
- State that the data is synthetic data.
- Summarize the pipeline shape in plain language.
- Name the validation outcome.
- Identify 2 practical strengths and 2 next hardening steps.
- Keep it under 350 words.
- Do not invent any metrics or claims beyond the JSON summary.

Aggregate validation summary:
```json
{
  "failed_validation_checks": [],
  "hosted_target": "Supabase project synthetic-education-data",
  "openai_input_policy": [
    "Only aggregate row counts and validation statuses are sent.",
    "No raw rows, emails, IDs, secrets, credentials, Canvas URLs, or private data are sent."
  ],
  "pipeline_shape": [
    "synthetic ASMA score artifacts",
    "synthetic Canvas-style course shell JSON extracts",
    "DuckDB raw/raw_canvas staging",
    "DuckDB marts",
    "Supabase lms staging tables",
    "Supabase analytics facts/dimensions",
    "Supabase public read-only views for assessment-intelligence"
  ],
  "source": "synthetic-education-data local mart exports",
  "synthetic_disclosure": "All rows are public-safe synthetic data.",
  "table_counts": {
    "canvas_roster_sql_extract": 2009,
    "dim_assignment": 14,
    "dim_course": 9,
    "dim_section": 174,
    "dim_student": 696,
    "dim_teacher": 35,
    "fact_assessment_score": 4018,
    "fact_lms_enrollment": 2009,
    "student_readiness": 2009,
    "validation_summary": 20
  },
  "validation_checks": 20,
  "validation_passes": 20
}
```
