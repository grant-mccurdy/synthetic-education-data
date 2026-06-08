#!/usr/bin/env python3
"""Draft a public-safe validation narrative for the Supabase pipeline.

Default mode is deterministic and local. Pass --call-api to send only aggregate
row counts and validation statuses to OpenAI.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ENV = PROJECT_ROOT.parents[1] / ".env"
DEFAULT_MARTS_DIR = PROJECT_ROOT / "data" / "marts"
DEFAULT_PROMPT_OUT = PROJECT_ROOT / "reports" / "supabase_pipeline_validation_prompt.md"
DEFAULT_NARRATIVE_OUT = PROJECT_ROOT / "reports" / "supabase_pipeline_validation_narrative.md"
RESPONSES_URL = "https://api.openai.com/v1/responses"

PUBLIC_SAFE_TABLES = (
    "canvas_roster_sql_extract",
    "dim_student",
    "dim_course",
    "dim_teacher",
    "dim_section",
    "dim_assignment",
    "student_readiness",
    "fact_assessment_score",
    "fact_lms_enrollment",
    "validation_summary",
)

SYSTEM_PROMPT = (
    "You write concise data pipeline validation notes for public-safe synthetic "
    "education data systems. State clearly that the data is synthetic. Do not "
    "claim the data describes real students, teachers, schools, or LMS records. "
    "Do not invent metrics beyond the supplied summary."
)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def build_summary(marts_dir: Path) -> dict[str, Any]:
    table_counts = {}
    for table_name in PUBLIC_SAFE_TABLES:
        path = marts_dir / f"{table_name}.csv"
        if path.exists():
            table_counts[table_name] = csv_row_count(path)

    validation_path = marts_dir / "validation_summary.csv"
    validation_rows = read_csv_rows(validation_path) if validation_path.exists() else []
    failed = [row["check_name"] for row in validation_rows if row.get("status") != "pass"]

    return {
        "source": "synthetic-education-data local mart exports",
        "synthetic_disclosure": "All rows are public-safe synthetic data.",
        "hosted_target": "Supabase project synthetic-education-data",
        "pipeline_shape": [
            "synthetic ASMA score artifacts",
            "synthetic Canvas-style course shell JSON extracts",
            "DuckDB raw/raw_canvas staging",
            "DuckDB marts",
            "Supabase lms staging tables",
            "Supabase analytics facts/dimensions",
            "Supabase public read-only views for assessment-intelligence",
        ],
        "table_counts": table_counts,
        "validation_checks": len(validation_rows),
        "validation_passes": len(validation_rows) - len(failed),
        "failed_validation_checks": failed,
        "openai_input_policy": [
            "Only aggregate row counts and validation statuses are sent.",
            "No raw rows, emails, IDs, secrets, credentials, Canvas URLs, or private data are sent.",
        ],
    }


def build_prompt(summary: dict[str, Any]) -> str:
    return (
        "Draft a short release-ready validation note for this synthetic "
        "education data pipeline.\n\n"
        "Requirements:\n"
        "- State that the data is synthetic data.\n"
        "- Summarize the pipeline shape in plain language.\n"
        "- Name the validation outcome.\n"
        "- Identify 2 practical strengths and 2 next hardening steps.\n"
        "- Keep it under 350 words.\n"
        "- Do not invent any metrics or claims beyond the JSON summary.\n\n"
        f"Aggregate validation summary:\n```json\n{json.dumps(summary, indent=2, sort_keys=True)}\n```"
    )


def call_openai(api_key: str, model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Authorization", f"Bearer {api_key}")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_obj = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API returned HTTP {exc.code}: {body[:500]}") from exc
    text = response_obj.get("output_text", "")
    if isinstance(text, str) and text.strip():
        return text.strip()
    parts: list[str] = []
    for item in response_obj.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(content.get("text", ""))
    output = "".join(parts).strip()
    if not output:
        raise RuntimeError("OpenAI response did not include output text.")
    return output


def local_narrative(summary: dict[str, Any]) -> str:
    failed = summary["failed_validation_checks"]
    status = "passed" if not failed else f"failed checks: {', '.join(failed)}"
    counts = summary["table_counts"]
    return f"""# Supabase Pipeline Validation Narrative

This note describes synthetic data only; it does not describe real students, teachers, schools, or LMS records.

The pipeline starts from generated ASMA score artifacts and synthetic Canvas-style course shell JSON extracts, builds a DuckDB warehouse, exports curated marts, and publishes a hosted Supabase serving layer for downstream `assessment-intelligence` extracts.

Validation status: {summary['validation_passes']} / {summary['validation_checks']} local validation checks {status}.

Key strengths:

- The pipeline separates reproducible local transformation from hosted serving, which makes the workflow inspectable and rebuildable.
- The hosted contract is narrow: `assessment-intelligence` can consume public read-only views instead of raw LMS-like staging tables.

Current aggregate load surface:

- Students: {counts.get('dim_student', 'n/a')}
- Canvas-style roster rows: {counts.get('canvas_roster_sql_extract', 'n/a')}
- Assessment fact rows: {counts.get('fact_assessment_score', 'n/a')}
- LMS enrollment fact rows: {counts.get('fact_lms_enrollment', 'n/a')}
- Student readiness rows: {counts.get('student_readiness', 'n/a')}

Next hardening steps:

- Keep Supabase post-load validation mandatory before any downstream report generation.
- Preserve the rule that OpenAI receives only aggregate validation metadata, never row-level LMS or assessment records.
"""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marts-dir", type=Path, default=DEFAULT_MARTS_DIR)
    parser.add_argument("--env-file", type=Path, default=WORKSPACE_ENV)
    parser.add_argument("--prompt-out", type=Path, default=DEFAULT_PROMPT_OUT)
    parser.add_argument("--narrative-out", type=Path, default=DEFAULT_NARRATIVE_OUT)
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4.1"))
    parser.add_argument("--call-api", action="store_true")
    args = parser.parse_args()

    env_values = parse_env_file(args.env_file)
    summary = build_summary(args.marts_dir)
    prompt = build_prompt(summary)
    write_text(
        args.prompt_out,
        "# Supabase Pipeline Validation Prompt Preview\n\n"
        "This prompt contains only synthetic aggregate validation metadata.\n\n"
        "## System Prompt\n\n"
        f"{SYSTEM_PROMPT}\n\n"
        "## User Prompt\n\n"
        f"{prompt}",
    )

    if args.call_api:
        api_key = os.environ.get("OPENAI_API_KEY") or env_values.get("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("OPENAI_API_KEY is required for --call-api.")
        narrative = call_openai(api_key, args.model, prompt)
    else:
        narrative = local_narrative(summary)
    write_text(args.narrative_out, narrative)
    print(f"Wrote prompt preview: {args.prompt_out}")
    print(f"Wrote validation narrative: {args.narrative_out}")


if __name__ == "__main__":
    main()
