#!/usr/bin/env python3
"""Validate public-safe synthetic math department artifacts."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DATA_DIR = ROOT / "data/synthetic"
STATE_PATH = SYNTHETIC_DATA_DIR / "synthetic_school_state.json"
GRADEBOOK_PATH = SYNTHETIC_DATA_DIR / "synthetic_asma_gradebook.csv"
COURSES_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_courses.csv"
SECTIONS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_sections.csv"
ENROLLMENTS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_enrollments.csv"

EXPECTED_COUNTS = {
    "students": 287,
    "teachers": 5,
    "courses": 9,
    "sections": 25,
    "enrollments": 287,
    "assignments": 14,
}

BANNED_PUBLIC_STRINGS = (
    "data/private",
    "data/raw",
    "data/calibration",
    "private_source_artifacts",
    "canvas_input",
    "raw institutional",
    "private reference",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_counts(state: dict[str, Any], gradebook_rows: list[dict[str, str]], courses: list[dict[str, str]], sections: list[dict[str, str]], enrollments: list[dict[str, str]]) -> None:
    require(state["schema_version"] == "synthetic_math_department_state_v1", "Unexpected state schema version.")
    require(len(state["students"]) == EXPECTED_COUNTS["students"], "Unexpected student count in state.")
    require(len(state["teachers"]) == EXPECTED_COUNTS["teachers"], "Unexpected teacher count in state.")
    require(len(state["courses"]) == EXPECTED_COUNTS["courses"], "Unexpected course count in state.")
    require(len(state["sections"]) == EXPECTED_COUNTS["sections"], "Unexpected section count in state.")
    require(len(state["enrollments"]) == EXPECTED_COUNTS["enrollments"], "Unexpected enrollment count in state.")
    require(len(state["assignments"]) == EXPECTED_COUNTS["assignments"], "Unexpected assignment count in state.")
    require(len(gradebook_rows) == EXPECTED_COUNTS["students"], "Unexpected gradebook row count.")
    require(len(courses) == EXPECTED_COUNTS["courses"], "Unexpected course CSV row count.")
    require(len(sections) == EXPECTED_COUNTS["sections"], "Unexpected section CSV row count.")
    require(len(enrollments) == EXPECTED_COUNTS["enrollments"], "Unexpected enrollment CSV row count.")


def validate_gradebook(gradebook_rows: list[dict[str, str]]) -> None:
    expected_fields = ["Student", "ID", "SIS User ID", "SIS Login ID", "Email", "Section", *[f"Assignment {idx:02d}" for idx in range(1, 15)]]
    require(list(gradebook_rows[0].keys()) == expected_fields, "Unexpected gradebook fields.")
    require(all(row["Assignment 01"] != "" for row in gradebook_rows), "Assignment 01 should be populated for every row.")
    require(
        sum(1 for row in gradebook_rows for idx in range(2, 15) if row[f"Assignment {idx:02d}"] != "") == 0,
        "Assignment 02 through Assignment 14 should remain blank in v1.",
    )
    require(all(re.fullmatch(r"[a-z][a-z]+(26|27|28|29)@schoolname\.org", row["Email"]) for row in gradebook_rows), "Unexpected synthetic email pattern.")

    for row in gradebook_rows:
        score = float(row["Assignment 01"])
        require(0 <= score <= 100, "Assignment 01 score outside [0, 100].")


def validate_enrollments(courses: list[dict[str, str]], sections: list[dict[str, str]], enrollments: list[dict[str, str]], gradebook_rows: list[dict[str, str]]) -> None:
    course_ids = {row["course_id"] for row in courses}
    eligible_course_ids = {row["course_id"] for row in courses if row["current_year_eligible"] == "True"}
    section_ids = {row["section_id"] for row in sections}
    teacher_ids = {row["teacher_id"] for row in sections}
    gradebook_student_ids = {row["SIS User ID"] for row in gradebook_rows}
    enrollment_student_ids = [row["SIS User ID"] for row in enrollments]

    require(set(enrollment_student_ids) == gradebook_student_ids, "Enrollment students do not match gradebook students.")
    require(len(enrollment_student_ids) == len(set(enrollment_student_ids)), "Each student should have exactly one active enrollment.")
    require(all(row["course_id"] in course_ids for row in sections), "A section references an unknown course.")
    require(all(row["course_id"] in eligible_course_ids for row in enrollments), "An enrollment references an ineligible course.")
    require(all(row["section_id"] in section_ids for row in enrollments), "An enrollment references an unknown section.")
    require(all(row["teacher_id"] in teacher_ids for row in enrollments), "An enrollment references an unknown teacher.")

    section_counts = {section_id: 0 for section_id in section_ids}
    for row in enrollments:
        section_counts[row["section_id"]] += 1
        require(row["enrollment_status"] == "active", "All v1 enrollments should be active.")
    require(all(count > 0 for count in section_counts.values()), "Sections should not be empty.")


def validate_public_safety(paths: tuple[Path, ...]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for banned in BANNED_PUBLIC_STRINGS:
            require(banned not in text, f"Public artifact contains banned string {banned!r}: {path}")


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    gradebook_rows = read_csv(GRADEBOOK_PATH)
    courses = read_csv(COURSES_PATH)
    sections = read_csv(SECTIONS_PATH)
    enrollments = read_csv(ENROLLMENTS_PATH)

    validate_counts(state, gradebook_rows, courses, sections, enrollments)
    validate_gradebook(gradebook_rows)
    validate_enrollments(courses, sections, enrollments, gradebook_rows)
    validate_public_safety((STATE_PATH, GRADEBOOK_PATH, COURSES_PATH, SECTIONS_PATH, ENROLLMENTS_PATH))
    print("Synthetic math department artifacts passed validation.")


if __name__ == "__main__":
    main()
