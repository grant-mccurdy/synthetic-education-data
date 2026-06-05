#!/usr/bin/env python3
"""Generate public-safe synthetic math department artifacts."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DATA_DIR = ROOT / "data/synthetic"
STATE_PATH = SYNTHETIC_DATA_DIR / "synthetic_school_state.json"
GRADEBOOK_PATH = SYNTHETIC_DATA_DIR / "synthetic_asma_gradebook.csv"
COURSES_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_courses.csv"
SECTIONS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_sections.csv"
ENROLLMENTS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_enrollments.csv"

SCHOOL_YEAR = "2025-2026"
SEED = 20260604
ROW_COUNT = 287
ASSIGNMENT_COUNT = 14

ATTENDANCE_CATEGORIES = (
    ("high", 0.40, (98, 2)),
    ("normal", 0.50, (92, 8)),
    ("at_risk", 0.10, (70, 30)),
)

FIRST_NAMES = (
    "Avery",
    "Blake",
    "Casey",
    "Devon",
    "Emerson",
    "Finley",
    "Gray",
    "Harper",
    "Indigo",
    "Jordan",
    "Kai",
    "Logan",
    "Morgan",
    "Noel",
    "Parker",
    "Quinn",
    "Riley",
    "Sage",
    "Taylor",
    "Vale",
)

LAST_NAMES = (
    "Stone",
    "Miller",
    "Rivera",
    "Nguyen",
    "Patel",
    "Brooks",
    "Chen",
    "Davis",
    "Evans",
    "Flores",
    "Garcia",
    "Hayes",
    "Ibrahim",
    "Johnson",
    "Kim",
    "Lewis",
    "Martinez",
    "Nelson",
    "Ortiz",
    "Price",
)

GRADE_BY_GRADUATION_YEAR = {"29": 9, "28": 10, "27": 11, "26": 12}
GRADUATION_YEAR_BY_GRADE = {grade: year for year, grade in GRADE_BY_GRADUATION_YEAR.items()}
GRADE_COUNTS = {9: 89, 10: 76, 11: 63, 12: 59}
CANVAS_SECTIONS = ("Section A", "Section B", "Section C", "Section D")

# Public-safe summary anchors for present-student Assignment 01 generation.
# These are generalized calibration parameters, not raw private scores.
ASSIGNMENT_01_SCORE_ANCHORS = {
    9: [(0.00, 7.0), (0.10, 18.0), (0.25, 29.0), (0.50, 42.0), (0.75, 56.0), (0.90, 70.0), (1.00, 90.0)],
    10: [(0.00, 10.0), (0.10, 23.0), (0.25, 34.0), (0.50, 47.0), (0.75, 62.0), (0.90, 76.0), (1.00, 95.0)],
    11: [(0.00, 12.0), (0.10, 26.0), (0.25, 38.0), (0.50, 52.0), (0.75, 68.0), (0.90, 82.0), (1.00, 98.0)],
    12: [(0.00, 14.0), (0.10, 30.0), (0.25, 43.0), (0.50, 58.0), (0.75, 74.0), (0.90, 88.0), (1.00, 100.0)],
}

COURSES = (
    {"course_id": "MATH-ALG1", "course_name": "Algebra 1", "track": "regular", "sequence_order": 1, "current_year_eligible": True},
    {"course_id": "MATH-GEOM", "course_name": "Geometry", "track": "regular", "sequence_order": 2, "current_year_eligible": True},
    {"course_id": "MATH-ALG2", "course_name": "Algebra 2", "track": "regular", "sequence_order": 3, "current_year_eligible": True},
    {"course_id": "MATH-ALG2-H", "course_name": "Honors Algebra 2", "track": "honors", "sequence_order": 3, "current_year_eligible": True},
    {"course_id": "MATH-PRECALC", "course_name": "Precalculus", "track": "regular", "sequence_order": 4, "current_year_eligible": True},
    {"course_id": "MATH-AP-PRECALC", "course_name": "AP Precalculus", "track": "ap", "sequence_order": 4, "current_year_eligible": True},
    {"course_id": "MATH-AP-CALC-AB", "course_name": "AP Calculus AB", "track": "ap", "sequence_order": 5, "current_year_eligible": True},
    {"course_id": "MATH-AP-CALC-BC", "course_name": "AP Calculus BC", "track": "ap", "sequence_order": 5, "current_year_eligible": True},
    {"course_id": "MATH-BEYOND-CORE", "course_name": "Beyond Core Math Sequence", "track": "beyond_core", "sequence_order": 6, "current_year_eligible": False},
)

GRADE_COURSE_COUNTS = {
    9: {"MATH-ALG1": 19, "MATH-GEOM": 49, "MATH-ALG2-H": 18, "MATH-AP-PRECALC": 3},
    10: {"MATH-ALG1": 2, "MATH-GEOM": 17, "MATH-ALG2": 24, "MATH-ALG2-H": 17, "MATH-PRECALC": 2, "MATH-AP-PRECALC": 11, "MATH-AP-CALC-AB": 3},
    11: {"MATH-GEOM": 5, "MATH-ALG2": 11, "MATH-ALG2-H": 8, "MATH-PRECALC": 7, "MATH-AP-PRECALC": 8, "MATH-AP-CALC-AB": 20, "MATH-AP-CALC-BC": 4},
    12: {"MATH-PRECALC": 7, "MATH-AP-PRECALC": 7, "MATH-AP-CALC-AB": 26, "MATH-AP-CALC-BC": 19},
}

SECTION_PLAN = (
    ("MATH-ALG1", 11, "TCH-001"),
    ("MATH-ALG1", 10, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-002"),
    ("MATH-GEOM", 12, "TCH-002"),
    ("MATH-GEOM", 11, "TCH-002"),
    ("MATH-ALG2", 18, "TCH-002"),
    ("MATH-ALG2", 17, "TCH-002"),
    ("MATH-ALG2-H", 11, "TCH-003"),
    ("MATH-ALG2-H", 11, "TCH-003"),
    ("MATH-ALG2-H", 11, "TCH-003"),
    ("MATH-ALG2-H", 10, "TCH-003"),
    ("MATH-PRECALC", 8, "TCH-003"),
    ("MATH-PRECALC", 8, "TCH-004"),
    ("MATH-AP-PRECALC", 10, "TCH-004"),
    ("MATH-AP-PRECALC", 10, "TCH-004"),
    ("MATH-AP-PRECALC", 9, "TCH-004"),
    ("MATH-AP-CALC-AB", 13, "TCH-004"),
    ("MATH-AP-CALC-AB", 12, "TCH-005"),
    ("MATH-AP-CALC-AB", 12, "TCH-005"),
    ("MATH-AP-CALC-AB", 12, "TCH-005"),
    ("MATH-AP-CALC-BC", 12, "TCH-005"),
    ("MATH-AP-CALC-BC", 11, "TCH-005"),
)

TEACHER_GROWTH_EFFECTS = {"TCH-001": -0.25, "TCH-002": 0.10, "TCH-003": 0.20, "TCH-004": -0.10, "TCH-005": 0.05}


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def build_grade_level_sequence() -> tuple[int, ...]:
    grades = [grade for grade, count in GRADE_COUNTS.items() for _ in range(count)]
    if len(grades) != ROW_COUNT:
        raise ValueError(f"Grade counts produce {len(grades)} rows, expected {ROW_COUNT}.")
    rng = random.Random(SEED + 17)
    rng.shuffle(grades)
    return tuple(grades)


GRADE_LEVEL_SEQUENCE = build_grade_level_sequence()


def interpolate_anchor_score(anchors: list[tuple[float, float]], probability: float) -> float:
    probability = clamp(probability, 0.0, 1.0)
    for idx, (upper_p, upper_score) in enumerate(anchors):
        if probability <= upper_p:
            if idx == 0:
                return upper_score
            lower_p, lower_score = anchors[idx - 1]
            if upper_p == lower_p:
                return upper_score
            fraction = (probability - lower_p) / (upper_p - lower_p)
            return lower_score * (1 - fraction) + upper_score * fraction
    return anchors[-1][1]


def draw_present_assignment_01_score(rng: random.Random, grade_level: int) -> float:
    anchors = ASSIGNMENT_01_SCORE_ANCHORS[grade_level]
    draw = rng.random()
    base_score = interpolate_anchor_score(anchors, draw)
    lower_score = interpolate_anchor_score(anchors, max(draw - 0.05, 0.0))
    upper_score = interpolate_anchor_score(anchors, min(draw + 0.05, 1.0))
    jitter_sd = clamp((upper_score - lower_score) * 0.12, 0.75, 3.0)
    score = base_score + rng.gauss(0, jitter_sd)
    return round(clamp(score, anchors[0][1], 100.0), 2)


def choose_attendance_category(rng: random.Random) -> tuple[str, tuple[int, int]]:
    draw = rng.random()
    cumulative = 0.0
    for name, probability, beta_params in ATTENDANCE_CATEGORIES:
        cumulative += probability
        if draw <= cumulative:
            return name, beta_params
    name, _probability, beta_params = ATTENDANCE_CATEGORIES[-1]
    return name, beta_params


def assignment_01_outcome(rng: random.Random, grade_level: int) -> tuple[float, dict[str, str | float | bool | int]]:
    potential_score = draw_present_assignment_01_score(rng, grade_level)
    category, beta_params = choose_attendance_category(rng)
    attendance_probability = rng.betavariate(*beta_params)
    present = rng.random() < attendance_probability
    observed_score = potential_score if present else 0.0
    return observed_score, {
        "grade_level": grade_level,
        "potential_assignment_01_score": potential_score,
        "attendance_category": category,
        "attendance_probability": round(attendance_probability, 4),
        "present_assignment_01": present,
        "assignment_01_score": observed_score,
    }


def class_size_band(size: int) -> str:
    if 7 <= size <= 12:
        return "small"
    if 13 <= size <= 18:
        return "standard"
    if 19 <= size <= 24:
        return "large"
    raise ValueError(f"Section target enrollment {size} is outside configured class-size bands.")


def teacher_label(teacher_id: str) -> str:
    number = int(teacher_id.split("-")[1])
    return f"Teacher {number:02d}"


def section_growth_effect(section_index: int) -> float:
    pattern = (-0.30, -0.20, -0.10, 0.00, 0.10, 0.20, 0.30)
    return pattern[(section_index - 1) % len(pattern)]


def synthetic_student_profile(idx: int) -> tuple[str, str, str, str]:
    first_name = FIRST_NAMES[(idx - 1) % len(FIRST_NAMES)]
    last_name = LAST_NAMES[((idx - 1) // len(FIRST_NAMES) + idx - 1) % len(LAST_NAMES)]
    graduation_year = GRADUATION_YEAR_BY_GRADE[GRADE_LEVEL_SEQUENCE[idx - 1]]
    section = CANVAS_SECTIONS[(idx - 1) % len(CANVAS_SECTIONS)]
    return first_name, last_name, graduation_year, section


def build_teacher_rows() -> list[dict[str, str | int | float]]:
    return [
        {
            "school_year": SCHOOL_YEAR,
            "teacher_id": teacher_id,
            "teacher_label": teacher_label(teacher_id),
            "target_section_load": 5,
            "teacher_growth_effect": effect,
        }
        for teacher_id, effect in sorted(TEACHER_GROWTH_EFFECTS.items())
    ]


def build_course_rows() -> list[dict[str, str | int | bool]]:
    return [dict(course) for course in COURSES]


def build_section_rows() -> list[dict[str, str | int | float]]:
    course_lookup = {course["course_id"]: course["course_name"] for course in COURSES}
    rows = []
    for idx, (course_id, target_enrollment, teacher_id) in enumerate(SECTION_PLAN, start=1):
        rows.append(
            {
                "school_year": SCHOOL_YEAR,
                "section_id": f"SEC-{idx:03d}",
                "course_id": course_id,
                "section_label": f"{course_lookup[course_id]} - Synthetic Section {idx:02d}",
                "teacher_id": teacher_id,
                "teacher_label": teacher_label(teacher_id),
                "period_label": f"Period {((idx - 1) % 6) + 1}",
                "target_enrollment": target_enrollment,
                "max_capacity": {"small": 12, "standard": 18, "large": 24}[class_size_band(target_enrollment)],
                "class_size_band": class_size_band(target_enrollment),
                "section_growth_effect": section_growth_effect(idx),
                "teacher_growth_effect": TEACHER_GROWTH_EFFECTS[teacher_id],
            }
        )
    return rows


def infer_grade_from_email(email: str) -> int:
    graduation_year = email.strip().split("@", 1)[0][-2:]
    if graduation_year not in GRADE_BY_GRADUATION_YEAR:
        raise ValueError(f"Could not infer grade from synthetic email: {email}")
    return GRADE_BY_GRADUATION_YEAR[graduation_year]


def assign_courses_to_students(rows: list[dict[str, str]]) -> dict[str, str]:
    rng = random.Random(SEED + 31)
    students_by_grade: dict[int, list[dict[str, str]]] = {grade: [] for grade in GRADE_COUNTS}
    for row in rows:
        students_by_grade[infer_grade_from_email(row["Email"])].append(row)

    student_course: dict[str, str] = {}
    for grade, expected_count in GRADE_COUNTS.items():
        students = students_by_grade[grade]
        if len(students) != expected_count:
            raise ValueError(f"Grade {grade} has {len(students)} students, expected {expected_count}.")
        rng.shuffle(students)
        cursor = 0
        for course_id, count in GRADE_COURSE_COUNTS[grade].items():
            for student in students[cursor : cursor + count]:
                student_course[student["SIS User ID"]] = course_id
            cursor += count
        if cursor != len(students):
            raise ValueError(f"Grade {grade} course counts assigned {cursor} students, expected {len(students)}.")
    return student_course


def build_enrollment_rows(rows: list[dict[str, str]], section_rows: list[dict[str, str | int | float]]) -> list[dict[str, str | int]]:
    rng = random.Random(SEED + 43)
    student_course = assign_courses_to_students(rows)
    students_by_course: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        students_by_course.setdefault(student_course[row["SIS User ID"]], []).append(row)

    sections_by_course: dict[str, list[dict[str, str | int | float]]] = {}
    for section in section_rows:
        sections_by_course.setdefault(str(section["course_id"]), []).append(section)

    enrollment_rows = []
    for course_id, students in sorted(students_by_course.items()):
        sections = sections_by_course.get(course_id, [])
        target_total = sum(int(section["target_enrollment"]) for section in sections)
        if target_total != len(students):
            raise ValueError(f"{course_id} has {len(students)} students but section targets sum to {target_total}.")
        rng.shuffle(students)
        cursor = 0
        for section in sections:
            section_size = int(section["target_enrollment"])
            for student in students[cursor : cursor + section_size]:
                enrollment_rows.append(
                    {
                        "school_year": SCHOOL_YEAR,
                        "Student": student["Student"],
                        "SIS User ID": student["SIS User ID"],
                        "grade_level": infer_grade_from_email(student["Email"]),
                        "course_id": course_id,
                        "section_id": section["section_id"],
                        "teacher_id": section["teacher_id"],
                        "enrollment_status": "active",
                    }
                )
            cursor += section_size
    return sorted(enrollment_rows, key=lambda row: str(row["SIS User ID"]))


def build_assignment_definitions() -> list[dict[str, str | int]]:
    assignments = []
    for idx in range(1, ASSIGNMENT_COUNT + 1):
        assignments.append(
            {
                "assignment_label": f"Assignment {idx:02d}",
                "sequence_index": idx,
                "school_year_offset": (idx - 1) // 2,
                "assessment_window": "beginning_of_year" if idx % 2 == 1 else "end_of_year",
                "population_status": "populated" if idx == 1 else "pending_rules",
            }
        )
    return assignments


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str | int | bool]], list[dict[str, str | int | float]], list[dict[str, str | int]]]:
    rng = random.Random(SEED)
    rows = []
    for idx in range(1, ROW_COUNT + 1):
        first_name, last_name, graduation_year, canvas_section = synthetic_student_profile(idx)
        grade_level = GRADE_BY_GRADUATION_YEAR[graduation_year]
        assignment_score, _assignment_profile = assignment_01_outcome(rng, grade_level)
        row = {
            "Student": f"Synthetic Student {idx:03d}",
            "ID": f"SYN-EXP-{idx:06d}",
            "SIS User ID": f"SYN-SIS-{idx:06d}",
            "SIS Login ID": f"synthetic{idx:03d}",
            "Email": f"{first_name[0].lower()}{last_name.lower()}{graduation_year}@schoolname.org",
            "Section": canvas_section,
            "Assignment 01": f"{assignment_score:g}",
        }
        for assignment_index in range(2, ASSIGNMENT_COUNT + 1):
            row[f"Assignment {assignment_index:02d}"] = ""
        rows.append(row)

    course_rows = build_course_rows()
    section_rows = build_section_rows()
    enrollment_rows = build_enrollment_rows(rows, section_rows)
    return rows, course_rows, section_rows, enrollment_rows


def parse_score(value: str | float | int | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def format_score(value: float | int | str | None) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value
    return f"{value:g}"


def build_synthetic_math_department_state(
    rows: list[dict[str, str]],
    course_rows: list[dict[str, str | int | bool]],
    section_rows: list[dict[str, str | int | float]],
    enrollment_rows: list[dict[str, str | int]],
) -> dict[str, Any]:
    students = []
    for row in rows:
        grade_level = infer_grade_from_email(row["Email"])
        students.append(
            {
                "student_key": row["SIS User ID"],
                "student_label": row["Student"],
                "export_id": row["ID"],
                "login_id": row["SIS Login ID"],
                "email": row["Email"],
                "grade_level": grade_level,
                "graduation_year_suffix": GRADUATION_YEAR_BY_GRADE[grade_level],
                "canvas_gradebook_section": row["Section"],
                "assignment_scores": {"Assignment 01": parse_score(row["Assignment 01"])},
            }
        )

    return {
        "schema_version": "synthetic_math_department_state_v1",
        "random_seed": SEED,
        "school_year": SCHOOL_YEAR,
        "students": sorted(students, key=lambda student: str(student["student_key"])),
        "teachers": build_teacher_rows(),
        "courses": course_rows,
        "sections": section_rows,
        "enrollments": enrollment_rows,
        "assessment_shells": [
            {
                "assessment_shell_id": "ASMA-ALL-MATH-2025-2026",
                "assessment_shell_label": "All School Math Assessment",
                "school_year": SCHOOL_YEAR,
                "source_system": "synthetic_canvas",
                "join_key": "email",
                "raw_gradebook_artifact": "synthetic_asma_gradebook.csv",
                "student_count": len(rows),
                "assignment_count": ASSIGNMENT_COUNT,
            }
        ],
        "assignments": build_assignment_definitions(),
        "derived_artifacts": [
            "synthetic_asma_gradebook.csv",
            "synthetic_math_courses.csv",
            "synthetic_math_sections.csv",
            "synthetic_math_enrollments.csv",
        ],
    }


def render_gradebook_rows_from_state(state: dict[str, Any]) -> list[dict[str, str]]:
    assignment_labels = [assignment["assignment_label"] for assignment in state["assignments"]]
    return [
        {
            "Student": student["student_label"],
            "ID": student["export_id"],
            "SIS User ID": student["student_key"],
            "SIS Login ID": student["login_id"],
            "Email": student["email"],
            "Section": student["canvas_gradebook_section"],
            **{label: format_score(student["assignment_scores"].get(label)) for label in assignment_labels},
        }
        for student in state["students"]
    ]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | float | int | bool]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")


def main() -> None:
    rows, course_rows, section_rows, enrollment_rows = build_rows()
    state = build_synthetic_math_department_state(rows, course_rows, section_rows, enrollment_rows)
    gradebook_rows = render_gradebook_rows_from_state(state)

    write_json(STATE_PATH, state)
    write_csv(
        GRADEBOOK_PATH,
        ["Student", "ID", "SIS User ID", "SIS Login ID", "Email", "Section", *[f"Assignment {idx:02d}" for idx in range(1, ASSIGNMENT_COUNT + 1)]],
        gradebook_rows,
    )
    write_csv(COURSES_PATH, ["course_id", "course_name", "track", "sequence_order", "current_year_eligible"], course_rows)
    write_csv(
        SECTIONS_PATH,
        [
            "school_year",
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
        ],
        section_rows,
    )
    write_csv(
        ENROLLMENTS_PATH,
        ["school_year", "Student", "SIS User ID", "grade_level", "course_id", "section_id", "teacher_id", "enrollment_status"],
        enrollment_rows,
    )


if __name__ == "__main__":
    main()
