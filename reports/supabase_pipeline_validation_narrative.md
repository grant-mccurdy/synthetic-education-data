# Supabase Pipeline Validation Narrative

This note describes synthetic data only; it does not describe real students, teachers, schools, or LMS records.

The pipeline starts from generated ASMA score artifacts and synthetic Canvas-style course shell JSON extracts, builds a DuckDB warehouse, exports curated marts, and publishes a hosted Supabase serving layer for downstream `assessment-intelligence` extracts.

Validation status: 20 / 20 local validation checks passed.

Key strengths:

- The pipeline separates reproducible local transformation from hosted serving, which makes the workflow inspectable and rebuildable.
- The hosted contract is narrow: `assessment-intelligence` can consume public read-only views instead of raw LMS-like staging tables.

Current aggregate load surface:

- Students: 696
- Canvas-style roster rows: 2009
- Assessment fact rows: 4018
- LMS enrollment fact rows: 2009
- Student readiness rows: 2009

Next hardening steps:

- Keep Supabase post-load validation mandatory before any downstream report generation.
- Preserve the rule that OpenAI receives only aggregate validation metadata, never row-level LMS or assessment records.
