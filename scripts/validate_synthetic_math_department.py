#!/usr/bin/env python3
"""Validate public-safe synthetic math department artifacts."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DATA_DIR = ROOT / "data/synthetic"
STATE_PATH = SYNTHETIC_DATA_DIR / "synthetic_school_state.json"
GRADEBOOK_PATH = SYNTHETIC_DATA_DIR / "synthetic_asma_gradebook.csv"
COURSES_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_courses.csv"
SECTIONS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_sections.csv"
ENROLLMENTS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_enrollments.csv"
ASSESSMENT_LONG_PATH = SYNTHETIC_DATA_DIR / "synthetic_assessment_scores_long.csv"
CANVAS_COURSE_PROFILES_DIR = SYNTHETIC_DATA_DIR / "canvas_course_profiles"
ASSESSMENT_SHELLS_DIR = SYNTHETIC_DATA_DIR / "assessment_shells"

SCHOOL_YEAR_COUNT = 7
ACTIVE_STUDENT_COUNT = 287
ASSIGNMENT_COUNT = 14
SYNTHETIC_EMAIL_DOMAIN = "schoolname.example"

BANNED_PUBLIC_STRINGS = (
    "/home/grant",
    "assessment-data",
    "data/private",
    "data/raw",
    "data/calibration",
    "private_source_artifacts",
    "canvas_input",
    "raw institutional",
    "private reference",
)

ATTENDANCE_SHARE_BOUNDS = {
    "high": (0.34, 0.46),
    "normal": (0.44, 0.56),
    "at_risk": (0.06, 0.14),
}

ALLOWED_TRANSITION_TYPES = {
    "initialize_readiness",
    "school_year_growth",
    "summer_atrophy",
    "absent_no_update",
}

ALLOWED_GENERATION_MODES = {
    "first_present_evidence_from_latent",
    "school_year_growth_from_latent_readiness",
    "summer_atrophy_from_latent_readiness",
    "absent_no_update",
}

ALLOWED_LATENT_TRANSITION_TYPES = {
    "initialize_latent_readiness",
    "school_year_growth",
    "summer_atrophy",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise AssertionError(f"Unexpected boolean value: {value}")


def optional_float(value: str) -> float | None:
    if value == "":
        return None
    return float(value)


def validate_counts(
    state: dict[str, Any],
    gradebook_rows: list[dict[str, str]],
    courses: list[dict[str, str]],
    sections: list[dict[str, str]],
    enrollments: list[dict[str, str]],
    assessment_scores: list[dict[str, str]],
) -> None:
    require(state["schema_version"] == "synthetic_math_department_state_v3", "Unexpected state schema version.")
    require(state["school_year_count"] == SCHOOL_YEAR_COUNT, "Unexpected school-year count.")
    require(state["active_student_count_per_year"] == ACTIVE_STUDENT_COUNT, "Unexpected active student count policy.")
    require(len(state["school_years"]) == SCHOOL_YEAR_COUNT, "Unexpected school_years length.")
    require(len(state["courses"]) == len(courses) == 9, "Unexpected course count.")
    require(len(state["teachers"]) == SCHOOL_YEAR_COUNT * 5, "Unexpected teacher-year count.")
    require(len(state["assignments"]) == ASSIGNMENT_COUNT, "Unexpected assignment count.")
    require(len(gradebook_rows) == len(state["students"]), "Combined gradebook should contain every synthetic student ever enrolled.")
    require(len(enrollments) == ACTIVE_STUDENT_COUNT * SCHOOL_YEAR_COUNT, "Unexpected enrollment row count.")
    require(len(assessment_scores) == ACTIVE_STUDENT_COUNT * ASSIGNMENT_COUNT, "Unexpected assessment-score long row count.")
    require(len(state["assessment_scores"]) == len(assessment_scores), "State and CSV assessment-score counts differ.")
    require(len(state["sections"]) == len(sections), "State and CSV section counts differ.")
    require(len(state["enrollments"]) == len(enrollments), "State and CSV enrollment counts differ.")


def validate_school_years_and_churn(state: dict[str, Any]) -> None:
    students = state["students"]
    by_year_active_ids: dict[str, set[str]] = {}
    for record in state["school_years"]:
        school_year = record["school_year"]
        offset = int(record["school_year_offset"])
        active_ids = {
            student["student_key"]
            for student in students
            for active_year in student["active_years"]
            if active_year["school_year"] == school_year
        }
        by_year_active_ids[school_year] = active_ids
        require(len(active_ids) == ACTIVE_STUDENT_COUNT, f"{school_year} should have {ACTIVE_STUDENT_COUNT} active students.")
        grade_counts = Counter(
            active_year["grade_level"]
            for student in students
            for active_year in student["active_years"]
            if active_year["school_year"] == school_year
        )
        require(dict(sorted(grade_counts.items())) == {int(k): int(v) for k, v in record["grade_counts"].items()}, f"Grade counts mismatch for {school_year}.")
        if offset == 0:
            require(record["new_freshman_count"] == 0, "Base year should not count new freshmen as churn.")
        else:
            previous_record = state["school_years"][offset - 1]
            require(record["new_freshman_count"] == previous_record["graduating_senior_count"], f"Freshman intake should replace prior seniors for {school_year}.")

    for student in students:
        active_years = student["active_years"]
        require(active_years, f"Student has no active years: {student['student_key']}")
        for idx, active_year in enumerate(active_years):
            grade = int(active_year["grade_level"])
            require(9 <= grade <= 12, f"Invalid grade level for {student['student_key']}.")
            if idx > 0:
                require(grade == int(active_years[idx - 1]["grade_level"]) + 1, f"Grade progression mismatch for {student['student_key']}.")
        first_year = active_years[0]
        if int(student["entry_school_year_offset"]) > 0:
            require(int(first_year["grade_level"]) == 9, f"New entrant should begin as grade 9: {student['student_key']}.")


def validate_gradebook(state: dict[str, Any], gradebook_rows: list[dict[str, str]]) -> None:
    expected_fields = ["Student", "ID", "SIS User ID", "SIS Login ID", "Email", "Section", *[f"Assignment {idx:02d}" for idx in range(1, ASSIGNMENT_COUNT + 1)]]
    require(list(gradebook_rows[0].keys()) == expected_fields, "Unexpected combined gradebook fields.")
    suffixes = sorted({student["graduation_year_suffix"] for student in state["students"]})
    suffix_pattern = "|".join(re.escape(suffix) for suffix in suffixes)
    email_pattern = rf"[a-z][a-z]+({suffix_pattern})@{re.escape(SYNTHETIC_EMAIL_DOMAIN)}"
    require(all(re.fullmatch(email_pattern, row["Email"]) for row in gradebook_rows), "Unexpected synthetic email pattern.")

    students_by_id = {student["student_key"]: student for student in state["students"]}
    require(set(row["SIS User ID"] for row in gradebook_rows) == set(students_by_id), "Gradebook student IDs do not match state.")

    for row in gradebook_rows:
        student = students_by_id[row["SIS User ID"]]
        expected_scores = student["assignment_scores"]
        for idx in range(1, ASSIGNMENT_COUNT + 1):
            label = f"Assignment {idx:02d}"
            value = row[label]
            if label in expected_scores:
                require(value != "", f"Active score missing for {student['student_key']} {label}.")
                score = float(value)
                require(0 <= score <= 100, f"Score outside [0, 100] for {student['student_key']} {label}.")
            else:
                require(value == "", f"Inactive-year score should be blank for {student['student_key']} {label}.")


def validate_yearly_assessment_shells(state: dict[str, Any]) -> tuple[Path, ...]:
    shell_paths = tuple(sorted(ASSESSMENT_SHELLS_DIR.glob("*/synthetic_asma_gradebook.csv")))
    require(len(shell_paths) == SCHOOL_YEAR_COUNT, "Unexpected yearly ASMA gradebook count.")
    students_by_id = {student["student_key"]: student for student in state["students"]}
    enrollments_by_year: dict[str, set[str]] = defaultdict(set)
    for enrollment in state["enrollments"]:
        enrollments_by_year[enrollment["school_year"]].add(enrollment["SIS User ID"])

    for record in state["school_years"]:
        path = ASSESSMENT_SHELLS_DIR / record["school_year"] / "synthetic_asma_gradebook.csv"
        rows = read_csv(path)
        labels = [record["beginning_assignment_label"], record["end_assignment_label"]]
        expected_fields = ["Student", "ID", "SIS User ID", "SIS Login ID", "Email", "Section", *labels]
        require(list(rows[0].keys()) == expected_fields, f"Unexpected ASMA shell fields for {record['school_year']}.")
        require(len(rows) == ACTIVE_STUDENT_COUNT, f"Unexpected ASMA shell row count for {record['school_year']}.")
        require(set(row["SIS User ID"] for row in rows) == enrollments_by_year[record["school_year"]], f"ASMA shell roster mismatch for {record['school_year']}.")
        for row in rows:
            student = students_by_id[row["SIS User ID"]]
            for label in labels:
                require(row[label] != "", f"Yearly ASMA shell missing score for {record['school_year']} {row['SIS User ID']} {label}.")
                require(label in student["assignment_scores"], f"Yearly ASMA shell score not in state for {row['SIS User ID']} {label}.")
    return shell_paths


def validate_assessment_scores(state: dict[str, Any], assessment_scores: list[dict[str, str]]) -> None:
    expected_fields = [
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
    ]
    require(list(assessment_scores[0].keys()) == expected_fields, "Unexpected assessment-score long fields.")
    assignment_lookup = {assignment["assignment_label"]: assignment for assignment in state["assignments"]}
    seen_keys = set()
    for row in assessment_scores:
        key = (row["sis_user_id"], row["assignment_label"])
        require(key not in seen_keys, f"Duplicate assessment score row: {key}.")
        seen_keys.add(key)
        assignment = assignment_lookup[row["assignment_label"]]
        require(row["school_year"] == assignment["school_year"], f"Score school year does not match assignment for {key}.")
        require(int(row["sequence_index"]) == int(assignment["sequence_index"]), f"Score sequence does not match assignment for {key}.")
        present = parse_bool(row["present"])
        score = float(row["observed_score"])
        latent_transition_type = row["latent_transition_type"]
        latent_readiness_before = optional_float(row["latent_readiness_before"])
        latent_readiness_after = optional_float(row["latent_readiness_after"])
        latent_transition_delta = optional_float(row["latent_transition_delta"])
        require(0 <= score <= 100, f"Observed score outside [0, 100] for {key}.")
        require(latent_transition_type in ALLOWED_LATENT_TRANSITION_TYPES, f"Unexpected latent transition type for {key}.")
        require(latent_readiness_after is not None and 1 <= latent_readiness_after <= 100, f"Latent readiness after should be bounded for {key}.")
        if latent_transition_type == "initialize_latent_readiness":
            require(latent_readiness_before is None, f"Initialized latent readiness should not have a prior latent value for {key}.")
            require(latent_transition_delta is None, f"Initialized latent readiness should not have a transition delta for {key}.")
        else:
            require(latent_readiness_before is not None and 1 <= latent_readiness_before <= 100, f"Latent readiness before should be bounded for {key}.")
            require(latent_transition_delta is not None, f"Latent transition should include a delta for {key}.")
        if present:
            require(score > 0, f"Present student should not receive zero for {key}.")
            require(optional_float(row["potential_score"]) is not None, f"Present score should include potential score for {key}.")
            require(optional_float(row["posterior_readiness_after"]) is not None, f"Present score should update readiness for {key}.")
            require(row["actual_transition_type"] != "absent_no_update", f"Present score should not use absent transition for {key}.")
        else:
            require(score == 0, f"Absent student should receive zero for {key}.")
            require(row["potential_score"] == "", f"Absent score should not include potential score for {key}.")
            require(row["posterior_readiness_after"] == "", f"Absent score should not update readiness for {key}.")
            require(row["growth_delta"] == "", f"Absent score should not include growth delta for {key}.")
            require(row["actual_transition_type"] == "absent_no_update", f"Absent score should use absent transition for {key}.")
            require(row["generation_mode"] == "absent_no_update", f"Absent score should use absent generation mode for {key}.")


def validate_longitudinal_method(state: dict[str, Any], assessment_scores: list[dict[str, str]]) -> None:
    student_attendance = Counter(student["attendance_category"] for student in state["students"])
    require(set(student_attendance) == set(ATTENDANCE_SHARE_BOUNDS), "Unexpected attendance categories.")
    for category, (lower, upper) in ATTENDANCE_SHARE_BOUNDS.items():
        share = student_attendance[category] / len(state["students"])
        require(lower <= share <= upper, f"Attendance category share outside expected range for {category}: {share:.3f}.")

    attendance_rows: dict[str, dict[str, int]] = defaultdict(lambda: {"rows": 0, "present": 0})
    transition_counts = Counter()
    latent_transition_counts = Counter()
    generation_counts = Counter()
    assignment_present_scores: dict[str, list[float]] = defaultdict(list)
    transition_deltas: dict[str, list[float]] = defaultdict(list)
    assignment_01_by_grade: dict[int, list[float]] = defaultdict(list)

    for row in assessment_scores:
        present = parse_bool(row["present"])
        observed_score = float(row["observed_score"])
        category = row["attendance_category"]
        transition = row["actual_transition_type"]
        latent_transition = row["latent_transition_type"]
        generation_mode = row["generation_mode"]

        require(transition in ALLOWED_TRANSITION_TYPES, f"Unexpected transition type: {transition}.")
        require(latent_transition in ALLOWED_LATENT_TRANSITION_TYPES, f"Unexpected latent transition type: {latent_transition}.")
        require(generation_mode in ALLOWED_GENERATION_MODES, f"Unexpected generation mode: {generation_mode}.")
        transition_counts[transition] += 1
        latent_transition_counts[latent_transition] += 1
        generation_counts[generation_mode] += 1

        attendance_rows[category]["rows"] += 1
        attendance_rows[category]["present"] += int(present)

        if present:
            assignment_present_scores[row["assignment_label"]].append(observed_score)
            if row["assignment_label"] == "Assignment 01":
                assignment_01_by_grade[int(row["grade_level"])].append(observed_score)
        if row["latent_transition_delta"] != "":
            transition_deltas[latent_transition].append(float(row["latent_transition_delta"]))

    require(ALLOWED_TRANSITION_TYPES.issubset(set(transition_counts)), "Missing expected transition type.")
    require(ALLOWED_LATENT_TRANSITION_TYPES.issubset(set(latent_transition_counts)), "Missing expected latent transition type.")
    require(ALLOWED_GENERATION_MODES.issubset(set(generation_counts)), "Missing expected generation mode.")

    attendance_rates = {
        category: values["present"] / values["rows"]
        for category, values in attendance_rows.items()
    }
    require(attendance_rates["high"] > attendance_rates["normal"] > attendance_rates["at_risk"], "Attendance rates should follow high > normal > at_risk.")
    require(attendance_rates["high"] >= 0.94, "High-attendance present rate is lower than expected.")
    require(0.86 <= attendance_rates["normal"] <= 0.96, "Normal-attendance present rate is outside expected range.")
    require(0.60 <= attendance_rates["at_risk"] <= 0.85, "At-risk present rate is outside expected range.")

    assignment_means = {
        label: sum(values) / len(values)
        for label, values in assignment_present_scores.items()
    }
    for idx in range(1, ASSIGNMENT_COUNT, 2):
        beginning_label = f"Assignment {idx:02d}"
        ending_label = f"Assignment {idx + 1:02d}"
        require(assignment_means[ending_label] > assignment_means[beginning_label], f"EOY mean should exceed BOY mean for {beginning_label}->{ending_label}.")
    for idx in range(2, ASSIGNMENT_COUNT, 2):
        ending_label = f"Assignment {idx:02d}"
        next_beginning_label = f"Assignment {idx + 1:02d}"
        require(assignment_means[next_beginning_label] < assignment_means[ending_label], f"Next BOY mean should reflect summer atrophy after {ending_label}.")

    school_growth_mean = sum(transition_deltas["school_year_growth"]) / len(transition_deltas["school_year_growth"])
    summer_atrophy_mean = sum(transition_deltas["summer_atrophy"]) / len(transition_deltas["summer_atrophy"])
    require(school_growth_mean > 0, "School-year growth deltas should be positive on average.")
    require(summer_atrophy_mean < 0, "Summer atrophy deltas should be negative on average.")

    require(set(assignment_01_by_grade) == {9, 10, 11, 12}, "Assignment 01 should have present scores for grades 9-12.")
    grade_values = []
    score_values = []
    for grade, scores in assignment_01_by_grade.items():
        grade_values.extend([grade] * len(scores))
        score_values.extend(scores)
    grade_mean = sum(grade_values) / len(grade_values)
    score_mean = sum(score_values) / len(score_values)
    slope_denominator = sum((grade - grade_mean) ** 2 for grade in grade_values)
    slope = sum((grade - grade_mean) * (score - score_mean) for grade, score in zip(grade_values, score_values)) / slope_denominator
    residual_sum_squares = sum((score - (score_mean + slope * (grade - grade_mean))) ** 2 for grade, score in zip(grade_values, score_values))
    total_sum_squares = sum((score - score_mean) ** 2 for score in score_values)
    r_squared = 1 - residual_sum_squares / total_sum_squares
    require(slope > 0, "Assignment 01 grade-level signal should be positive.")
    require(r_squared < 0.15, "Assignment 01 grade-level signal should remain weak.")


def validate_enrollments_and_sections(courses: list[dict[str, str]], sections: list[dict[str, str]], enrollments: list[dict[str, str]]) -> None:
    course_ids = {row["course_id"] for row in courses}
    section_lookup = {(row["school_year"], row["section_id"]): row for row in sections}
    enrollments_by_year_student: dict[tuple[str, str], int] = defaultdict(int)
    section_counts: dict[tuple[str, str], int] = defaultdict(int)

    for enrollment in enrollments:
        school_year = enrollment["school_year"]
        student_id = enrollment["SIS User ID"]
        key = (school_year, student_id)
        enrollments_by_year_student[key] += 1
        require(enrollment["course_id"] in course_ids, f"Enrollment references unknown course: {enrollment}.")
        require((school_year, enrollment["section_id"]) in section_lookup, f"Enrollment references unknown section: {enrollment}.")
        require(enrollment["enrollment_status"] == "active", "All generated enrollments should be active.")
        require(9 <= int(enrollment["grade_level"]) <= 12, f"Enrollment grade outside 9-12: {enrollment}.")
        section_counts[(school_year, enrollment["section_id"])] += 1

    require(all(count == 1 for count in enrollments_by_year_student.values()), "Each active student should have one math enrollment per school year.")
    per_year_counts = Counter(row["school_year"] for row in enrollments)
    require(all(count == ACTIVE_STUDENT_COUNT for count in per_year_counts.values()), "Each school year should have the configured active enrollment count.")
    require(set(section_counts) == set(section_lookup), "Every generated section should have enrollment rows.")
    for key, section in section_lookup.items():
        require(section_counts[key] == int(section["target_enrollment"]), f"Section target mismatch for {key}.")
        require(1 <= int(section["target_enrollment"]) <= int(section["max_capacity"]) <= 24, f"Section capacity policy mismatch for {key}.")

    teacher_loads = Counter((row["school_year"], row["teacher_id"]) for row in sections)
    require(max(teacher_loads.values()) <= 6, "Teacher section load should not exceed rare six-section load.")

    enrollments_by_student: dict[str, list[dict[str, str]]] = defaultdict(list)
    for enrollment in enrollments:
        enrollments_by_student[enrollment["SIS User ID"]].append(enrollment)
    for student_id, student_enrollments in enrollments_by_student.items():
        history = sorted(student_enrollments, key=lambda row: int(row["school_year_offset"]))
        for idx, enrollment in enumerate(history):
            if enrollment["course_id"] == "MATH-BEYOND-CORE":
                require(idx > 0, f"Beyond Core requires a prior course for {student_id}.")
                previous_course = history[idx - 1]["course_id"]
                require(previous_course in {"MATH-AP-CALC-BC", "MATH-BEYOND-CORE"}, f"Beyond Core should only follow AP Calculus BC or itself for {student_id}.")


def validate_canvas_course_profiles(
    state: dict[str, Any],
    courses: list[dict[str, str]],
    sections: list[dict[str, str]],
    enrollments: list[dict[str, str]],
    gradebook_rows: list[dict[str, str]],
) -> tuple[Path, ...]:
    profile_paths = tuple(sorted(CANVAS_COURSE_PROFILES_DIR.rglob("*.json")))
    require(not tuple(CANVAS_COURSE_PROFILES_DIR.glob("*.json")), "Canvas profiles should be year-scoped, not flat root JSON files.")
    expected_profile_count = sum(len(record["course_counts"]) for record in state["school_years"])
    require(len(profile_paths) == expected_profile_count, "Unexpected Canvas course profile count.")

    courses_by_id = {row["course_id"]: row for row in courses}
    section_lookup = {(row["school_year"], row["section_id"]): row for row in sections}
    sections_by_year_course: dict[tuple[str, str], set[str]] = defaultdict(set)
    for section in sections:
        sections_by_year_course[(section["school_year"], section["course_id"])].add(section["section_id"])

    enrollment_lookup = {(row["school_year"], row["section_id"], row["SIS User ID"]) for row in enrollments}
    gradebook_student_ids = {row["SIS User ID"] for row in gradebook_rows}
    profile_enrollment_keys = []

    expected_artifacts = {f"canvas_course_profiles/{path.relative_to(CANVAS_COURSE_PROFILES_DIR).as_posix()}" for path in profile_paths}
    require(expected_artifacts.issubset(set(state["derived_artifacts"])), "State derived artifacts do not list every Canvas course profile.")

    for path in profile_paths:
        profile = json.loads(path.read_text(encoding="utf-8"))
        school_year = profile["school_year"]
        course_id = profile["course_id"]
        require(path.relative_to(CANVAS_COURSE_PROFILES_DIR).as_posix() == f"{school_year}/{course_id}.json", f"Canvas profile path mismatch: {path}.")
        require(course_id in courses_by_id, f"Canvas profile references unknown course: {course_id}.")
        require(profile["course_name"] == courses_by_id[course_id]["course_name"], f"Course name mismatch for {course_id}.")
        require(profile["track"] == courses_by_id[course_id]["track"], f"Track mismatch for {course_id}.")
        require(profile["source_system"] == "synthetic_canvas", f"Unexpected source system for {course_id}.")

        seen_profile_sections = set()
        for profile_section in profile["sections"]:
            section_id = profile_section["section_id"]
            section_key = (school_year, section_id)
            require(section_key in section_lookup, f"Canvas profile references unknown section: {section_key}.")
            require(section_id in sections_by_year_course[(school_year, course_id)], f"Section {section_id} does not belong to {school_year} {course_id}.")
            require(profile_section["teacher"]["teacher_id"] == section_lookup[section_key]["teacher_id"], f"Teacher mismatch for {section_key}.")
            seen_profile_sections.add(section_id)

            for student in profile_section["students"]:
                student_id = student["SIS User ID"]
                profile_enrollment_keys.append((school_year, section_id, student_id))
                require(student_id in gradebook_student_ids, f"Canvas profile student missing from combined gradebook: {student_id}.")
                require((school_year, section_id, student_id) in enrollment_lookup, f"Canvas profile student lacks matching enrollment: {school_year}, {section_id}, {student_id}.")
                require(student["Email"].endswith(f"@{SYNTHETIC_EMAIL_DOMAIN}"), f"Unexpected profile email domain for {student_id}.")
                require(student["enrollment_status"] == "active", f"Unexpected enrollment status for {student_id}.")

        require(seen_profile_sections == sections_by_year_course[(school_year, course_id)], f"Canvas profile section set mismatch for {school_year} {course_id}.")

    require(set(profile_enrollment_keys) == enrollment_lookup, "Canvas profile enrollments do not match canonical enrollments.")
    require(len(profile_enrollment_keys) == len(set(profile_enrollment_keys)), "Each student-year enrollment should appear in exactly one Canvas profile section.")
    return profile_paths


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
    assessment_scores = read_csv(ASSESSMENT_LONG_PATH)

    validate_counts(state, gradebook_rows, courses, sections, enrollments, assessment_scores)
    validate_school_years_and_churn(state)
    validate_gradebook(state, gradebook_rows)
    shell_paths = validate_yearly_assessment_shells(state)
    validate_assessment_scores(state, assessment_scores)
    validate_longitudinal_method(state, assessment_scores)
    validate_enrollments_and_sections(courses, sections, enrollments)
    profile_paths = validate_canvas_course_profiles(state, courses, sections, enrollments, gradebook_rows)
    validate_public_safety((STATE_PATH, GRADEBOOK_PATH, COURSES_PATH, SECTIONS_PATH, ENROLLMENTS_PATH, ASSESSMENT_LONG_PATH, *shell_paths, *profile_paths))
    print("Synthetic math department artifacts passed validation.")


if __name__ == "__main__":
    main()
