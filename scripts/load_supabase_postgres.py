#!/usr/bin/env python3
"""Load validated synthetic education exports into Postgres/Supabase."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import subprocess
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ENV = PROJECT_ROOT.parents[1] / ".env"
DEFAULT_MARTS_DIR = PROJECT_ROOT / "data" / "marts"
DEFAULT_SCHEMA_FILE = PROJECT_ROOT / "sql" / "postgres" / "00_analytics_schema.sql"
SUPABASE_API_BASE = "https://api.supabase.com"
SUPABASE_PROJECT_NAME = "synthetic-education-data"
LOADER_VERSION = "synthetic_supabase_loader_v2"


@dataclass(frozen=True)
class TableSpec:
    schema_name: str
    table_name: str
    csv_name: str | None
    columns: tuple[str, ...]

    @property
    def full_name(self) -> str:
        return f"{self.schema_name}.{self.table_name}"


DIRECT_TABLES = (
    TableSpec(
        "analytics",
        "dim_student",
        "dim_student.csv",
        (
            "student_dim_id",
            "sis_user_id",
            "student_label",
            "export_id",
            "canvas_gradebook_section",
            "graduation_year",
            "graduation_year_suffix",
            "cohort_label",
            "entry_school_year",
            "entry_school_year_offset",
            "graduation_school_year",
            "graduation_school_year_offset",
            "attendance_category",
            "attendance_probability",
            "latest_academic_profile_status",
            "latest_posterior_readiness",
            "latest_latent_readiness",
            "latest_present_score",
        ),
    ),
    TableSpec(
        "analytics",
        "dim_course",
        "dim_course.csv",
        (
            "course_dim_id",
            "course_id",
            "course_name",
            "course_track",
            "sequence_order",
            "current_year_eligible",
        ),
    ),
    TableSpec(
        "analytics",
        "dim_teacher",
        "dim_teacher.csv",
        (
            "teacher_dim_id",
            "school_year",
            "teacher_id",
            "teacher_label",
            "target_section_load",
            "teacher_growth_effect",
        ),
    ),
    TableSpec(
        "analytics",
        "dim_section",
        "dim_section.csv",
        (
            "section_dim_id",
            "school_year",
            "school_year_offset",
            "section_id",
            "section_label",
            "period_label",
            "course_id",
            "course_dim_id",
            "teacher_id",
            "teacher_dim_id",
            "teacher_label",
            "target_enrollment",
            "max_capacity",
            "class_size_band",
            "section_growth_effect",
            "teacher_growth_effect",
        ),
    ),
    TableSpec(
        "analytics",
        "dim_assignment",
        "dim_assignment.csv",
        (
            "assignment_dim_id",
            "assignment_label",
            "sequence_index",
            "school_year",
            "school_year_offset",
            "assessment_window",
            "transition_type",
            "population_status",
        ),
    ),
    TableSpec(
        "analytics",
        "student_readiness",
        "student_readiness.csv",
        (
            "school_year",
            "school_year_offset",
            "sis_user_id",
            "student_label",
            "grade_level",
            "course_id",
            "course_name",
            "course_track",
            "section_id",
            "section_label",
            "teacher_id",
            "teacher_label",
            "attendance_category",
            "attendance_probability",
            "boy_assignment_label",
            "eoy_assignment_label",
            "boy_score",
            "eoy_score",
            "present_boy",
            "present_eoy",
            "modeled_eoy_growth_delta",
            "posterior_readiness_after_eoy",
            "latent_readiness_after_boy",
            "latent_readiness_after_eoy",
            "latent_eoy_transition_delta",
            "eoy_generation_mode",
            "eoy_transition_type",
            "eoy_academic_profile_status",
            "observed_growth_delta",
            "academic_profile_status",
        ),
    ),
    TableSpec(
        "analytics",
        "fact_assessment_score",
        "fact_assessment_score.csv",
        (
            "assessment_score_fact_id",
            "student_dim_id",
            "course_dim_id",
            "section_dim_id",
            "teacher_dim_id",
            "assignment_dim_id",
            "school_year",
            "school_year_offset",
            "sis_user_id",
            "course_id",
            "section_id",
            "teacher_id",
            "assignment_label",
            "sequence_index",
            "assessment_window",
            "expected_transition_type",
            "actual_transition_type",
            "generation_mode",
            "population_status",
            "score",
            "present_student_score",
            "potential_score",
            "posterior_readiness_after",
            "growth_delta",
            "latent_transition_type",
            "latent_readiness_before",
            "latent_readiness_after",
            "latent_transition_delta",
            "is_populated",
            "is_present",
            "is_nonparticipation_zero",
        ),
    ),
    TableSpec(
        "analytics",
        "fact_lms_enrollment",
        "fact_lms_enrollment.csv",
        (
            "lms_enrollment_fact_id",
            "student_dim_id",
            "course_dim_id",
            "section_dim_id",
            "teacher_dim_id",
            "extraction_batch_id",
            "source_system",
            "school_year",
            "canvas_course_id",
            "course_id",
            "section_id",
            "teacher_id",
            "sis_user_id",
            "grade_level",
            "enrollment_status",
            "is_active_enrollment",
            "reconciliation_status",
        ),
    ),
    TableSpec(
        "analytics",
        "validation_summary",
        "validation_summary.csv",
        ("check_name", "observed_value", "expected_value", "status"),
    ),
)

LMS_COURSES = TableSpec(
    "lms",
    "canvas_courses",
    None,
    (
        "extraction_batch_id",
        "source_system",
        "school_year",
        "canvas_course_id",
        "course_id",
        "course_name",
        "course_track",
    ),
)
LMS_SECTIONS = TableSpec(
    "lms",
    "canvas_sections",
    None,
    (
        "extraction_batch_id",
        "canvas_course_id",
        "course_id",
        "section_id",
        "school_year",
        "section_label",
        "period_label",
        "teacher_id",
        "teacher_label",
    ),
)
LMS_ENROLLMENTS = TableSpec(
    "lms",
    "canvas_enrollments",
    "canvas_roster_sql_extract.csv",
    (
        "extraction_batch_id",
        "canvas_course_id",
        "school_year",
        "course_id",
        "section_id",
        "sis_user_id",
        "student_label",
        "email",
        "grade_level",
        "enrollment_status",
    ),
)

ROSTER_COLUMNS = (
    "extraction_batch_id",
    "source_system",
    "school_year",
    "canvas_course_id",
    "course_id",
    "course_name",
    "course_track",
    "section_id",
    "section_label",
    "period_label",
    "teacher_id",
    "teacher_label",
    "sis_user_id",
    "student_label",
    "email",
    "grade_level",
    "enrollment_status",
)

LOAD_ORDER = (
    LMS_COURSES,
    LMS_SECTIONS,
    LMS_ENROLLMENTS,
    *DIRECT_TABLES,
)

EXPECTED_COUNTS = {
    "lms.canvas_courses": 62,
    "lms.canvas_sections": 174,
    "lms.canvas_enrollments": 2009,
    "analytics.dim_student": 696,
    "analytics.dim_course": 9,
    "analytics.dim_teacher": 35,
    "analytics.dim_section": 174,
    "analytics.dim_assignment": 14,
    "analytics.student_readiness": 2009,
    "analytics.fact_assessment_score": 4018,
    "analytics.fact_lms_enrollment": 2009,
    "analytics.validation_summary": 20,
    "public.course_section_performance": 174,
    "public.assignment_growth_by_course": 149,
    "public.nonparticipation_by_group": 462,
    "public.lms_enrollment_reconciliation": 2009,
    "public.student_readiness_extract": 2009,
}

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote_identifier(identifier: str) -> str:
    if not IDENTIFIER_RE.match(identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")
    return f'"{identifier}"'


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


def env_first(names: tuple[str, ...], env_file_values: dict[str, str]) -> str:
    for name in names:
        value = os.environ.get(name) or env_file_values.get(name)
        if value:
            return value
    return ""


def csv_rows(path: Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing export: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        if header != expected_columns:
            raise ValueError(f"Header mismatch for {path.name}: expected {expected_columns}, observed {header}")
        return list(reader)


def derive_lms_tables(roster_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    courses: OrderedDict[str, dict[str, str]] = OrderedDict()
    sections: OrderedDict[tuple[str, str], dict[str, str]] = OrderedDict()
    enrollments: list[dict[str, str]] = []

    for row in roster_rows:
        courses.setdefault(
            row["canvas_course_id"],
            {column: row[column] for column in LMS_COURSES.columns},
        )
        section_key = (row["canvas_course_id"], row["school_year"], row["section_id"])
        sections.setdefault(
            section_key,
            {column: row[column] for column in LMS_SECTIONS.columns},
        )
        enrollments.append({column: row[column] for column in LMS_ENROLLMENTS.columns})

    return {
        LMS_COURSES.full_name: list(courses.values()),
        LMS_SECTIONS.full_name: list(sections.values()),
        LMS_ENROLLMENTS.full_name: enrollments,
    }


def validate_inputs(marts_dir: Path, schema_file: Path) -> dict[str, list[dict[str, str]]]:
    if not schema_file.exists():
        raise FileNotFoundError(f"Missing schema file: {schema_file}")

    rows_by_table: dict[str, list[dict[str, str]]] = {}
    roster_rows = csv_rows(marts_dir / "canvas_roster_sql_extract.csv", ROSTER_COLUMNS)
    rows_by_table.update(derive_lms_tables(roster_rows))
    for spec in DIRECT_TABLES:
        if spec.csv_name is None:
            continue
        rows_by_table[spec.full_name] = csv_rows(marts_dir / spec.csv_name, spec.columns)
    return rows_by_table


def current_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


def sql_literal(value: Any) -> str:
    if value is None or value == "":
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def insert_sql(spec: TableSpec, rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    table_identifier = f"{quote_identifier(spec.schema_name)}.{quote_identifier(spec.table_name)}"
    column_list = ", ".join(quote_identifier(column) for column in spec.columns)
    values = []
    for row in rows:
        values.append("(" + ", ".join(sql_literal(row[column]) for column in spec.columns) + ")")
    return f"INSERT INTO {table_identifier} ({column_list}) VALUES\n" + ",\n".join(values) + ";"


def chunked(rows: list[dict[str, str]], size: int = 250) -> list[list[dict[str, str]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def copy_rows(cursor: Any, spec: TableSpec, rows: list[dict[str, str]]) -> None:
    table_identifier = f"{quote_identifier(spec.schema_name)}.{quote_identifier(spec.table_name)}"
    column_list = ", ".join(quote_identifier(column) for column in spec.columns)
    copy_sql = f"COPY {table_identifier} ({column_list}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(spec.columns), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)
    with cursor.copy(copy_sql) as copy:
        copy.write(buffer.read())


def find_supabase_project_ref(access_token: str, project_name: str) -> str:
    try:
        import requests
    except ImportError as exc:
        raise SystemExit("requests is required for Management API mode. Run `make postgres-install`.") from exc

    response = requests.get(
        f"{SUPABASE_API_BASE}/v1/projects",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if not response.ok:
        raise SystemExit(f"Could not list Supabase projects: status {response.status_code}")
    matches = [project for project in response.json() if project.get("name") == project_name]
    if len(matches) != 1:
        raise SystemExit(f"Expected one Supabase project named {project_name!r}; found {len(matches)}.")
    return matches[0]["id"]


class ManagementApiExecutor:
    def __init__(self, access_token: str, project_ref: str) -> None:
        try:
            import requests
        except ImportError as exc:
            raise SystemExit("requests is required for Management API mode. Run `make postgres-install`.") from exc

        self.requests = requests
        self.project_ref = project_ref
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def execute(self, sql: str) -> list[dict[str, Any]]:
        response = self.requests.post(
            f"{SUPABASE_API_BASE}/v1/projects/{self.project_ref}/database/query",
            headers=self.headers,
            json={"query": sql},
            timeout=120,
        )
        if not response.ok:
            raise SystemExit(f"Supabase query failed with status {response.status_code}: {response.text[:300]}")
        payload = response.json()
        return payload if isinstance(payload, list) else []

    def read(self, sql: str) -> list[dict[str, Any]]:
        response = self.requests.post(
            f"{SUPABASE_API_BASE}/v1/projects/{self.project_ref}/database/query/read-only",
            headers=self.headers,
            json={"query": sql},
            timeout=60,
        )
        if not response.ok:
            raise SystemExit(f"Supabase read-only query failed with status {response.status_code}: {response.text[:300]}")
        payload = response.json()
        return payload if isinstance(payload, list) else []


def validation_checks(read: Callable[[str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for table_name, expected_count in EXPECTED_COUNTS.items():
        rows = read(f"SELECT COUNT(*)::bigint AS row_count FROM {table_name};")
        observed = int(rows[0]["row_count"]) if rows else -1
        checks.append(
            {
                "check_name": f"{table_name}_row_count",
                "observed": observed,
                "expected": expected_count,
                "status": "pass" if observed == expected_count else "fail",
            }
        )

    rows = read(
        "SELECT COUNT(*)::bigint AS row_count "
        "FROM analytics.validation_summary "
        "WHERE status <> 'pass';"
    )
    failed_validation_rows = int(rows[0]["row_count"]) if rows else -1
    checks.append(
        {
            "check_name": "analytics.validation_summary_all_pass",
            "observed": failed_validation_rows,
            "expected": 0,
            "status": "pass" if failed_validation_rows == 0 else "fail",
        }
    )
    return checks


def insert_pipeline_run(execute: Callable[[str], list[dict[str, Any]]], rows_by_table: dict[str, list[dict[str, str]]], status: str) -> None:
    run_id = datetime.now(timezone.utc).strftime("synthetic_education_data_%Y%m%dT%H%M%SZ")
    table_counts = {name: len(rows) for name, rows in sorted(rows_by_table.items())}
    sql = (
        "INSERT INTO analytics.pipeline_runs "
        "(run_id, source_project, loader_version, source_commit, table_counts, validation_status) "
        "VALUES ("
        f"{sql_literal(run_id)}, "
        f"{sql_literal('synthetic-education-data')}, "
        f"{sql_literal(LOADER_VERSION)}, "
        f"{sql_literal(current_commit())}, "
        f"{sql_literal(json.dumps(table_counts, sort_keys=True))}::jsonb, "
        f"{sql_literal(status)}"
        ");"
    )
    execute(sql)


def fail_if_validation_failed(checks: list[dict[str, Any]]) -> None:
    failed = [check for check in checks if check["status"] != "pass"]
    if failed:
        names = ", ".join(check["check_name"] for check in failed)
        raise SystemExit(f"Supabase validation failed: {names}")


def print_validation(checks: list[dict[str, Any]]) -> None:
    print("Supabase validation checks:")
    for check in checks:
        print(f"- {check['check_name']}: {check['status']} ({check['observed']} / {check['expected']})")


def load_with_postgres(database_url: str, schema_file: Path, rows_by_table: dict[str, list[dict[str, str]]]) -> None:
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("Missing psycopg. Run `make postgres-install`.") from exc

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_file.read_text(encoding="utf-8"))
            for spec in LOAD_ORDER:
                copy_rows(cursor, spec, rows_by_table[spec.full_name])
                print(f"Loaded {spec.full_name}: {len(rows_by_table[spec.full_name])} rows")

            def execute(sql: str) -> list[dict[str, Any]]:
                cursor.execute(sql)
                return []

            def read(sql: str) -> list[dict[str, Any]]:
                cursor.execute(sql)
                columns = [column.name for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

            checks = validation_checks(read)
            fail_if_validation_failed(checks)
            insert_pipeline_run(execute, rows_by_table, "pass")
            execute("NOTIFY pgrst, 'reload schema';")
            execute("SELECT pg_notification_queue_usage();")
            print_validation(checks)
        connection.commit()


def load_with_management_api(project_ref: str, access_token: str, schema_file: Path, rows_by_table: dict[str, list[dict[str, str]]]) -> None:
    executor = ManagementApiExecutor(access_token, project_ref)
    executor.execute(schema_file.read_text(encoding="utf-8"))
    for spec in LOAD_ORDER:
        rows = rows_by_table[spec.full_name]
        for chunk in chunked(rows):
            executor.execute(insert_sql(spec, chunk))
        print(f"Loaded {spec.full_name}: {len(rows)} rows")
    checks = validation_checks(executor.read)
    fail_if_validation_failed(checks)
    insert_pipeline_run(executor.execute, rows_by_table, "pass")
    executor.execute("NOTIFY pgrst, 'reload schema';")
    executor.execute("SELECT pg_notification_queue_usage();")
    print_validation(checks)


def validate_hosted(args: argparse.Namespace, env_values: dict[str, str]) -> None:
    access_token = env_first(("SUPABASE_ACCESS_TOKEN",), env_values)
    if not access_token:
        raise SystemExit("SUPABASE_ACCESS_TOKEN is required for hosted validation without a database URL.")
    project_ref = args.supabase_project_ref or find_supabase_project_ref(access_token, args.supabase_project_name)
    executor = ManagementApiExecutor(access_token, project_ref)
    checks = validation_checks(executor.read)
    print_validation(checks)
    fail_if_validation_failed(checks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marts-dir", type=Path, default=DEFAULT_MARTS_DIR)
    parser.add_argument("--schema-file", type=Path, default=DEFAULT_SCHEMA_FILE)
    parser.add_argument("--env-file", type=Path, default=WORKSPACE_ENV)
    parser.add_argument("--database-url", default="")
    parser.add_argument("--method", choices=("auto", "postgres", "management-api"), default="auto")
    parser.add_argument("--supabase-project-name", default=SUPABASE_PROJECT_NAME)
    parser.add_argument("--supabase-project-ref", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    env_values = parse_env_file(args.env_file)
    database_url = args.database_url or env_first(
        ("SUPABASE_DATABASE_URL", "SUPABASE_DB_URL", "PROJECT1_SUPABASE_DB_URL"),
        env_values,
    )

    if args.validate_only:
        validate_hosted(args, env_values)
        return

    rows_by_table = validate_inputs(args.marts_dir, args.schema_file)
    print("Validated Supabase load inputs:")
    for spec in LOAD_ORDER:
        print(f"- {spec.full_name}: {len(rows_by_table[spec.full_name])} rows")

    if args.dry_run:
        print("Dry run only; no hosted connection was opened.")
        return

    method = args.method
    if method == "auto":
        method = "postgres" if database_url else "management-api"

    if method == "postgres":
        if not database_url:
            raise SystemExit("Set SUPABASE_DATABASE_URL or pass --database-url for Postgres mode.")
        load_with_postgres(database_url, args.schema_file, rows_by_table)
    else:
        access_token = env_first(("SUPABASE_ACCESS_TOKEN",), env_values)
        if not access_token:
            raise SystemExit("SUPABASE_ACCESS_TOKEN is required for Management API mode.")
        project_ref = args.supabase_project_ref or find_supabase_project_ref(access_token, args.supabase_project_name)
        load_with_management_api(project_ref, access_token, args.schema_file, rows_by_table)

    print("Loaded synthetic LMS staging, analytics marts, validation, and public views into Supabase.")


if __name__ == "__main__":
    main()
