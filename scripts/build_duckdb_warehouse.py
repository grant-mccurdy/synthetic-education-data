#!/usr/bin/env python3
"""Build a local DuckDB analytics warehouse and public-safe mart exports."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DATA_DIR = ROOT / "data/synthetic"
STATE_PATH = SYNTHETIC_DATA_DIR / "synthetic_school_state.json"
GRADEBOOK_PATH = SYNTHETIC_DATA_DIR / "synthetic_asma_gradebook.csv"
COURSES_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_courses.csv"
SECTIONS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_sections.csv"
ENROLLMENTS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_enrollments.csv"
ASSESSMENT_LONG_PATH = SYNTHETIC_DATA_DIR / "synthetic_assessment_scores_long.csv"
CANVAS_COURSE_PROFILES_DIR = SYNTHETIC_DATA_DIR / "canvas_course_profiles"
SQL_DIR = ROOT / "sql"
MART_SQL_DIR = SQL_DIR / "marts"
DEFAULT_DB_PATH = ROOT / "warehouse/synthetic_math.duckdb"
DEFAULT_EXPORT_DIR = ROOT / "data/marts"
EXTRACTION_BATCH_ID = "synthetic_canvas_profile_extract_v2"

MART_EXPORTS = (
    "student_assessment_long",
    "canvas_roster_sql_extract",
    "student_readiness",
    "dim_student",
    "dim_course",
    "dim_teacher",
    "dim_section",
    "dim_assignment",
    "fact_assessment_score",
    "assignment_growth",
    "course_section_summary",
    "missingness_attendance",
    "teacher_section_effects",
    "lms_to_sql_roster_reconciliation",
    "canvas_course_pipeline_audit",
    "fact_lms_enrollment",
    "validation_summary",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="DuckDB database path to build.")
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR, help="Directory for mart CSV exports.")
    parser.add_argument("--no-export", action="store_true", help="Build the database without writing mart CSVs.")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def optional_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def optional_int(value: Any) -> int | None:
    if value in ("", None):
        return None
    return int(value)


def optional_bool(value: Any) -> bool | None:
    if value in ("", None):
        return None
    return parse_bool(value)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def execute_sql_file(connection: Any, path: Path) -> None:
    connection.execute(path.read_text(encoding="utf-8"))


def insert_rows(connection: Any, table_name: str, columns: tuple[str, ...], rows: Iterable[tuple[Any, ...]]) -> None:
    rows = list(rows)
    if not rows:
        return
    with tempfile.TemporaryDirectory(prefix="synthetic_math_duckdb_load_") as temp_dir:
        stage_path = Path(temp_dir) / f"{table_name.replace('.', '_')}.csv"
        with stage_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)
        escaped_path = str(stage_path).replace("'", "''")
        connection.execute(f"COPY {table_name} FROM '{escaped_path}' (HEADER, DELIMITER ',')")


def gradebook_rows() -> list[tuple[Any, ...]]:
    rows = []
    for row in read_csv_rows(GRADEBOOK_PATH):
        rows.append(
            (
                row["Student"],
                row["ID"],
                row["SIS User ID"],
                row["SIS Login ID"],
                row["Email"],
                row["Section"],
                *[optional_float(row[f"Assignment {idx:02d}"]) for idx in range(1, 15)],
            )
        )
    return rows


def course_rows() -> list[tuple[Any, ...]]:
    return [
        (
            row["course_id"],
            row["course_name"],
            row["track"],
            optional_int(row["sequence_order"]),
            parse_bool(row["current_year_eligible"]),
        )
        for row in read_csv_rows(COURSES_PATH)
    ]


def section_rows() -> list[tuple[Any, ...]]:
    return [
        (
            row["school_year"],
            optional_int(row["school_year_offset"]),
            row["section_id"],
            row["course_id"],
            row["section_label"],
            row["teacher_id"],
            row["teacher_label"],
            row["period_label"],
            optional_int(row["target_enrollment"]),
            optional_int(row["max_capacity"]),
            row["class_size_band"],
            optional_float(row["section_growth_effect"]),
            optional_float(row["teacher_growth_effect"]),
        )
        for row in read_csv_rows(SECTIONS_PATH)
    ]


def enrollment_rows() -> list[tuple[Any, ...]]:
    return [
        (
            row["school_year"],
            optional_int(row["school_year_offset"]),
            row["Student"],
            row["SIS User ID"],
            optional_int(row["grade_level"]),
            row["course_id"],
            row["section_id"],
            row["teacher_id"],
            row["enrollment_status"],
        )
        for row in read_csv_rows(ENROLLMENTS_PATH)
    ]


def student_rows(state: dict[str, Any]) -> list[tuple[Any, ...]]:
    rows = []
    for student in state["students"]:
        profile = student["assessment_profile"]
        rows.append(
            (
                student["student_key"],
                student["student_label"],
                student["export_id"],
                student["login_id"],
                student["email"],
                student["canvas_gradebook_section"],
                optional_int(student["graduation_year"]),
                student["graduation_year_suffix"],
                student["cohort_label"],
                student["entry_school_year"],
                optional_int(student["entry_school_year_offset"]),
                student["graduation_school_year"],
                optional_int(student["graduation_school_year_offset"]),
                profile["attendance_category"],
                optional_float(profile["attendance_probability"]),
                profile["latest_academic_profile_status"],
                optional_float(profile["latest_posterior_readiness"]),
                optional_float(profile["latest_latent_readiness"]),
                optional_float(profile["latest_present_score"]),
            )
        )
    return rows


def school_year_rows(state: dict[str, Any]) -> list[tuple[Any, ...]]:
    return [
        (
            row["school_year"],
            optional_int(row["school_year_offset"]),
            row["beginning_assignment_label"],
            row["end_assignment_label"],
            optional_int(row["active_student_count"]),
            optional_int(row["new_freshman_count"]),
            optional_int(row["graduating_senior_count"]),
            optional_int(row["section_count"]),
        )
        for row in state["school_years"]
    ]


def teacher_rows(state: dict[str, Any]) -> list[tuple[Any, ...]]:
    return [
        (
            row["school_year"],
            row["teacher_id"],
            row["teacher_label"],
            optional_int(row["target_section_load"]),
            optional_float(row["teacher_growth_effect"]),
        )
        for row in state["teachers"]
    ]


def assignment_rows(state: dict[str, Any]) -> list[tuple[Any, ...]]:
    return [
        (
            row["assignment_label"],
            optional_int(row["sequence_index"]),
            row["school_year"],
            optional_int(row["school_year_offset"]),
            row["assessment_window"],
            row["transition_type"],
            row["population_status"],
        )
        for row in state["assignments"]
    ]


def assessment_score_rows() -> list[tuple[Any, ...]]:
    return [
        (
            row["school_year"],
            optional_int(row["school_year_offset"]),
            row["assignment_label"],
            optional_int(row["sequence_index"]),
            row["assessment_window"],
            row["expected_transition_type"],
            row["actual_transition_type"],
            row["generation_mode"],
            row["sis_user_id"],
            row["student_label"],
            optional_int(row["grade_level"]),
            row["course_id"],
            row["course_track"],
            row["section_id"],
            row["teacher_id"],
            row["attendance_category"],
            optional_float(row["attendance_probability"]),
            optional_bool(row["present"]),
            optional_float(row["observed_score"]),
            optional_float(row["potential_score"]),
            optional_float(row["posterior_readiness_after"]),
            optional_float(row["growth_delta"]),
            row["latent_transition_type"],
            optional_float(row["latent_readiness_before"]),
            optional_float(row["latent_readiness_after"]),
            optional_float(row["latent_transition_delta"]),
            row["academic_profile_status"],
        )
        for row in read_csv_rows(ASSESSMENT_LONG_PATH)
    ]


def canvas_profiles() -> list[tuple[Path, dict[str, Any]]]:
    profiles = []
    for path in sorted(CANVAS_COURSE_PROFILES_DIR.rglob("*.json")):
        profiles.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return profiles


def canvas_course_rows() -> list[tuple[Any, ...]]:
    rows = []
    for path, profile in canvas_profiles():
        rows.append(
            (
                profile["canvas_course_id"],
                profile["course_id"],
                profile["course_name"],
                profile["school_year"],
                profile["source_system"],
                profile["track"],
                str(path.relative_to(ROOT)),
                EXTRACTION_BATCH_ID,
            )
        )
    return rows


def canvas_section_rows() -> list[tuple[Any, ...]]:
    rows = []
    for _, profile in canvas_profiles():
        for section in profile["sections"]:
            rows.append(
                (
                    profile["canvas_course_id"],
                    profile["school_year"],
                    profile["course_id"],
                    section["section_id"],
                    section["section_label"],
                    section["period_label"],
                    section["teacher"]["teacher_id"],
                    section["teacher"]["teacher_label"],
                    EXTRACTION_BATCH_ID,
                )
            )
    return rows


def canvas_enrollment_rows() -> list[tuple[Any, ...]]:
    rows = []
    for _, profile in canvas_profiles():
        for section in profile["sections"]:
            for student in section["students"]:
                rows.append(
                    (
                        profile["canvas_course_id"],
                        profile["school_year"],
                        profile["course_id"],
                        section["section_id"],
                        student["SIS User ID"],
                        student["Student"],
                        student["Email"],
                        optional_int(student["grade_level"]),
                        student["enrollment_status"],
                        EXTRACTION_BATCH_ID,
                    )
                )
    return rows


def load_raw_tables(connection: Any) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    insert_rows(
        connection,
        "raw.gradebook",
        (
            "student_label",
            "export_id",
            "sis_user_id",
            "sis_login_id",
            "email",
            "canvas_gradebook_section",
            "assignment_01",
            "assignment_02",
            "assignment_03",
            "assignment_04",
            "assignment_05",
            "assignment_06",
            "assignment_07",
            "assignment_08",
            "assignment_09",
            "assignment_10",
            "assignment_11",
            "assignment_12",
            "assignment_13",
            "assignment_14",
        ),
        gradebook_rows(),
    )
    insert_rows(
        connection,
        "raw.students",
        (
            "sis_user_id",
            "student_label",
            "export_id",
            "sis_login_id",
            "email",
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
        student_rows(state),
    )
    insert_rows(
        connection,
        "raw.school_years",
        (
            "school_year",
            "school_year_offset",
            "beginning_assignment_label",
            "end_assignment_label",
            "active_student_count",
            "new_freshman_count",
            "graduating_senior_count",
            "section_count",
        ),
        school_year_rows(state),
    )
    insert_rows(
        connection,
        "raw.courses",
        ("course_id", "course_name", "track", "sequence_order", "current_year_eligible"),
        course_rows(),
    )
    insert_rows(
        connection,
        "raw.sections",
        (
            "school_year",
            "school_year_offset",
            "section_id",
            "course_id",
            "section_label",
            "teacher_id",
            "teacher_label",
            "period_label",
            "target_enrollment",
            "max_capacity",
            "class_size_band",
            "section_growth_effect",
            "teacher_growth_effect",
        ),
        section_rows(),
    )
    insert_rows(
        connection,
        "raw.enrollments",
        ("school_year", "school_year_offset", "student_label", "sis_user_id", "grade_level", "course_id", "section_id", "teacher_id", "enrollment_status"),
        enrollment_rows(),
    )
    insert_rows(
        connection,
        "raw.teachers",
        ("school_year", "teacher_id", "teacher_label", "target_section_load", "teacher_growth_effect"),
        teacher_rows(state),
    )
    insert_rows(
        connection,
        "raw.assignments",
        ("assignment_label", "sequence_index", "school_year", "school_year_offset", "assessment_window", "transition_type", "population_status"),
        assignment_rows(state),
    )
    insert_rows(
        connection,
        "raw.assessment_scores",
        (
            "school_year",
            "school_year_offset",
            "assignment_label",
            "sequence_index",
            "assessment_window",
            "expected_transition_type",
            "actual_transition_type",
            "generation_mode",
            "sis_user_id",
            "student_label",
            "grade_level",
            "course_id",
            "course_track",
            "section_id",
            "teacher_id",
            "attendance_category",
            "attendance_probability",
            "present",
            "observed_score",
            "potential_score",
            "posterior_readiness_after",
            "growth_delta",
            "latent_transition_type",
            "latent_readiness_before",
            "latent_readiness_after",
            "latent_transition_delta",
            "academic_profile_status",
        ),
        assessment_score_rows(),
    )
    insert_rows(
        connection,
        "raw_canvas.courses",
        ("canvas_course_id", "course_id", "course_name", "school_year", "source_system", "track", "profile_path", "extraction_batch_id"),
        canvas_course_rows(),
    )
    insert_rows(
        connection,
        "raw_canvas.sections",
        ("canvas_course_id", "school_year", "course_id", "section_id", "section_label", "period_label", "teacher_id", "teacher_label", "extraction_batch_id"),
        canvas_section_rows(),
    )
    insert_rows(
        connection,
        "raw_canvas.enrollments",
        ("canvas_course_id", "school_year", "course_id", "section_id", "sis_user_id", "student_label", "email", "grade_level", "enrollment_status", "extraction_batch_id"),
        canvas_enrollment_rows(),
    )


def build_marts(connection: Any) -> None:
    for path in sorted(MART_SQL_DIR.glob("*.sql")):
        execute_sql_file(connection, path)


def export_marts(connection: Any, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    for table_name in MART_EXPORTS:
        output_path = export_dir / f"{table_name}.csv"
        escaped_path = str(output_path).replace("'", "''")
        connection.execute(
            f"COPY (SELECT * FROM mart.{table_name}) TO '{escaped_path}' (HEADER, DELIMITER ',')"
        )


def print_summary(connection: Any, db_path: Path, export_dir: Path | None) -> None:
    print(f"Built DuckDB warehouse: {db_path}")
    if export_dir:
        print(f"Exported mart CSVs: {export_dir}")
    validation_rows = connection.execute("SELECT check_name, status FROM mart.validation_summary ORDER BY check_name").fetchall()
    failed = [name for name, status in validation_rows if status != "pass"]
    if failed:
        raise AssertionError(f"Warehouse validation checks failed: {', '.join(failed)}")
    print(f"Warehouse validation checks passed: {len(validation_rows)}")


def main() -> None:
    args = parse_args()
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit(
            "DuckDB is required for the warehouse target. Install it with: "
            "python3 -m pip install -r requirements-analytics.txt"
        ) from exc

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(args.db_path))
    print("Building DuckDB schema...", flush=True)
    execute_sql_file(connection, SQL_DIR / "00_schema.sql")
    print("Loading raw synthetic data...", flush=True)
    load_raw_tables(connection)
    print("Building analytics marts...", flush=True)
    build_marts(connection)
    if args.no_export:
        print_summary(connection, args.db_path, None)
    else:
        print("Exporting mart CSVs...", flush=True)
        export_marts(connection, args.export_dir)
        print_summary(connection, args.db_path, args.export_dir)
    connection.close()


if __name__ == "__main__":
    main()
