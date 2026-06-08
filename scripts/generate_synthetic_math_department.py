#!/usr/bin/env python3
"""Generate public-safe synthetic math department artifacts."""

from __future__ import annotations

import csv
import json
import math
import random
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
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

BASE_START_YEAR = 2025
SCHOOL_YEAR_COUNT = 7
SEED = 20260604
ACTIVE_STUDENT_COUNT = 287
ASSIGNMENT_COUNT = 14
SYNTHETIC_EMAIL_DOMAIN = "schoolname.example"

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

INITIAL_GRADE_COUNTS = {9: 89, 10: 76, 11: 63, 12: 59}
INITIAL_GRADE_COURSE_COUNTS = {
    9: {"MATH-ALG1": 19, "MATH-GEOM": 49, "MATH-ALG2-H": 18, "MATH-AP-PRECALC": 3},
    10: {"MATH-ALG1": 2, "MATH-GEOM": 17, "MATH-ALG2": 24, "MATH-ALG2-H": 17, "MATH-PRECALC": 2, "MATH-AP-PRECALC": 11, "MATH-AP-CALC-AB": 3},
    11: {"MATH-GEOM": 5, "MATH-ALG2": 11, "MATH-ALG2-H": 8, "MATH-PRECALC": 7, "MATH-AP-PRECALC": 8, "MATH-AP-CALC-AB": 20, "MATH-AP-CALC-BC": 4},
    12: {"MATH-PRECALC": 7, "MATH-AP-PRECALC": 7, "MATH-AP-CALC-AB": 26, "MATH-AP-CALC-BC": 19},
}

CANVAS_SECTIONS = ("Section A", "Section B", "Section C", "Section D")

# Public-safe summary anchors for present-student beginning-of-year score generation.
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
    {"course_id": "MATH-BEYOND-CORE", "course_name": "Beyond Core Math Sequence", "track": "beyond_core", "sequence_order": 6, "current_year_eligible": True},
)

TEACHER_GROWTH_EFFECTS = {"TCH-001": -0.25, "TCH-002": 0.10, "TCH-003": 0.20, "TCH-004": -0.10, "TCH-005": 0.05}
TEACHER_COURSE_PREFERENCES = {
    "MATH-ALG1": ("TCH-001",),
    "MATH-GEOM": ("TCH-001", "TCH-002"),
    "MATH-ALG2": ("TCH-002",),
    "MATH-ALG2-H": ("TCH-003",),
    "MATH-PRECALC": ("TCH-003", "TCH-004"),
    "MATH-AP-PRECALC": ("TCH-004",),
    "MATH-AP-CALC-AB": ("TCH-004", "TCH-005"),
    "MATH-AP-CALC-BC": ("TCH-005",),
    "MATH-BEYOND-CORE": ("TCH-005", "TCH-004"),
}

LONGITUDINAL_MODEL_VERSION = "longitudinal_score_engine_v3"
GRADE_PRIOR_SHIFT_PER_GRADE = 1.7953
READINESS_PRIOR_BASE_GRADE_9 = 45.0
READINESS_PRIOR_SD = 14.0
MEASUREMENT_ERROR_SD = 6.0
GROWTH_NOISE_SD = 2.5
OBSERVATION_NOISE_SD = 3.0
REGRESSION_TO_MEAN_STRENGTH = 0.08
REGRESSION_TO_MEAN_CAP = 3.0

GRADE_BASE_GROWTH = {9: 6.0, 10: 5.3, 11: 4.6, 12: 3.9}
TRACK_READINESS_EFFECTS = {"regular": 0.0, "honors": 4.0, "ap": 6.0, "beyond_core": 8.0}
TRACK_GROWTH_EFFECTS = {"regular": 0.0, "honors": 0.50, "ap": 0.25, "beyond_core": 0.0}


@dataclass(frozen=True)
class AssessmentContext:
    school_year: str
    school_year_offset: int
    assignment_label: str
    sequence_index: int
    assessment_window: str
    expected_transition_type: str
    grade_level: int
    course_id: str
    course_track: str
    section_id: str
    teacher_id: str
    instructor_effect: float
    section_effect: float


@dataclass(frozen=True)
class AssessmentResult:
    observed_score: float
    potential_score: float | None
    present: bool
    generation_mode: str
    actual_transition_type: str
    posterior_readiness_after: float | None
    growth_delta: float | None
    latent_transition_type: str
    latent_readiness_before: float | None
    latent_readiness_after: float
    latent_transition_delta: float | None
    academic_profile_status: str


def school_year_for_offset(offset: int) -> str:
    return f"{BASE_START_YEAR + offset}-{BASE_START_YEAR + offset + 1}"


def school_year_end(offset: int) -> int:
    return BASE_START_YEAR + offset + 1


def assignment_label_for_sequence(sequence_index: int) -> str:
    return f"Assignment {sequence_index:02d}"


def grade_for_graduation_year(graduation_year: int, school_year_offset: int) -> int:
    return 12 - (graduation_year - school_year_end(school_year_offset))


def active_in_year(student: dict[str, Any], school_year_offset: int) -> bool:
    grade = grade_for_graduation_year(int(student["graduation_year"]), school_year_offset)
    return 9 <= grade <= 12 and int(student["entry_school_year_offset"]) <= school_year_offset


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def build_initial_grade_level_sequence() -> tuple[int, ...]:
    grades = [grade for grade, count in INITIAL_GRADE_COUNTS.items() for _ in range(count)]
    if len(grades) != ACTIVE_STUDENT_COUNT:
        raise ValueError(f"Initial grade counts produce {len(grades)} rows, expected {ACTIVE_STUDENT_COUNT}.")
    rng = random.Random(SEED + 17)
    rng.shuffle(grades)
    return tuple(grades)


INITIAL_GRADE_LEVEL_SEQUENCE = build_initial_grade_level_sequence()


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


def draw_present_beginning_score(rng: random.Random, grade_level: int) -> float:
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


def readiness_prior_mean(grade_level: int, course_track: str) -> float:
    grade_shift = (grade_level - 9) * GRADE_PRIOR_SHIFT_PER_GRADE
    track_shift = TRACK_READINESS_EFFECTS[course_track]
    return READINESS_PRIOR_BASE_GRADE_9 + grade_shift + track_shift


def bayesian_readiness_update(prior_mean: float, observed_score: float) -> float:
    prior_precision = 1 / (READINESS_PRIOR_SD**2)
    observation_precision = 1 / (MEASUREMENT_ERROR_SD**2)
    posterior = ((prior_mean * prior_precision) + (observed_score * observation_precision)) / (prior_precision + observation_precision)
    return clamp(posterior, 0.0, 100.0)


def transition_growth(rng: random.Random, posterior_readiness: float, context: AssessmentContext) -> float:
    base_growth = GRADE_BASE_GROWTH[context.grade_level]
    track_growth = TRACK_GROWTH_EFFECTS[context.course_track]
    regression_target = readiness_prior_mean(context.grade_level, context.course_track) + base_growth
    regression_to_mean = clamp(
        (regression_target - posterior_readiness) * REGRESSION_TO_MEAN_STRENGTH,
        -REGRESSION_TO_MEAN_CAP,
        REGRESSION_TO_MEAN_CAP,
    )
    return (
        base_growth
        + track_growth
        + context.instructor_effect
        + context.section_effect
        + regression_to_mean
        + rng.gauss(0, GROWTH_NOISE_SD)
    )


def summer_atrophy_loss(rng: random.Random, posterior_readiness: float, context: AssessmentContext) -> float:
    readiness_adjustment = clamp((58.0 - posterior_readiness) * 0.045, -1.1, 1.8)
    track_adjustment = {"regular": 0.0, "honors": -0.35, "ap": -0.55, "beyond_core": -0.70}[context.course_track]
    loss = 2.4 + readiness_adjustment + track_adjustment + rng.gauss(0, 1.1)
    return clamp(loss, 0.0, 7.0)


def initialize_latent_readiness(rng: random.Random, context: AssessmentContext) -> float:
    score = draw_present_beginning_score(rng, context.grade_level)
    score += TRACK_READINESS_EFFECTS[context.course_track] * 0.30
    if context.assessment_window == "end_of_year":
        score += GRADE_BASE_GROWTH[context.grade_level] * 0.85
        score += TRACK_GROWTH_EFFECTS[context.course_track]
        score += context.instructor_effect + context.section_effect
    return round(clamp(score, 1.0, 100.0), 4)


def evolve_latent_readiness(
    rng: random.Random,
    previous_latent_readiness: float | None,
    context: AssessmentContext,
) -> tuple[float | None, float, float | None, str]:
    if previous_latent_readiness is None:
        latent_after = initialize_latent_readiness(rng, context)
        return None, latent_after, None, "initialize_latent_readiness"

    if context.expected_transition_type == "summer_atrophy":
        loss = summer_atrophy_loss(rng, previous_latent_readiness, context)
        latent_after = round(clamp(previous_latent_readiness - loss, 1.0, 100.0), 4)
        transition_type = "summer_atrophy"
    else:
        growth = transition_growth(rng, previous_latent_readiness, context)
        latent_after = round(clamp(previous_latent_readiness + growth, 1.0, 100.0), 4)
        transition_type = "school_year_growth"

    return (
        round(previous_latent_readiness, 4),
        latent_after,
        round(latent_after - previous_latent_readiness, 4),
        transition_type,
    )


def observed_readiness_prior_mean(previous_observed_readiness: float | None, context: AssessmentContext) -> float:
    context_prior = readiness_prior_mean(context.grade_level, context.course_track)
    if previous_observed_readiness is None:
        return context_prior
    return (previous_observed_readiness * 0.85) + (context_prior * 0.15)


def generate_assessment_score(
    rng: random.Random,
    student: dict[str, Any],
    previous_latent_readiness: float | None,
    previous_observed_readiness: float | None,
    previous_present_score: float | None,
    context: AssessmentContext,
) -> tuple[AssessmentResult, float, float | None, float | None]:
    attendance_probability = float(student["attendance_probability"])
    latent_before, latent_after, latent_delta, latent_transition_type = evolve_latent_readiness(
        rng,
        previous_latent_readiness,
        context,
    )
    present = rng.random() < attendance_probability

    if not present:
        status = "pending_no_present_scores" if previous_observed_readiness is None else "observed_readiness_unchanged_absent"
        result = AssessmentResult(
            observed_score=0.0,
            potential_score=None,
            present=False,
            generation_mode="absent_no_update",
            actual_transition_type="absent_no_update",
            posterior_readiness_after=None,
            growth_delta=None,
            latent_transition_type=latent_transition_type,
            latent_readiness_before=latent_before,
            latent_readiness_after=latent_after,
            latent_transition_delta=latent_delta,
            academic_profile_status=status,
        )
        return result, latent_after, previous_observed_readiness, previous_present_score

    observed_score = round(clamp(latent_after + rng.gauss(0, OBSERVATION_NOISE_SD), 1.0, 100.0), 2)
    prior_mean = observed_readiness_prior_mean(previous_observed_readiness, context)
    posterior_readiness = bayesian_readiness_update(prior_mean, observed_score)
    if previous_observed_readiness is None:
        actual_transition_type = "initialize_readiness"
        generation_mode = "first_present_evidence_from_latent"
        academic_profile_status = f"initialized_{context.assignment_label.lower().replace(' ', '_')}"
    else:
        actual_transition_type = latent_transition_type
        generation_mode = f"{latent_transition_type}_from_latent_readiness"
        academic_profile_status = f"updated_{context.assignment_label.lower().replace(' ', '_')}"

    growth_delta = None if previous_present_score is None else round(observed_score - previous_present_score, 4)
    result = AssessmentResult(
        observed_score=observed_score,
        potential_score=round(latent_after, 2),
        present=True,
        generation_mode=generation_mode,
        actual_transition_type=actual_transition_type,
        posterior_readiness_after=round(posterior_readiness, 4),
        growth_delta=growth_delta,
        latent_transition_type=latent_transition_type,
        latent_readiness_before=latent_before,
        latent_readiness_after=latent_after,
        latent_transition_delta=latent_delta,
        academic_profile_status=academic_profile_status,
    )
    return result, latent_after, posterior_readiness, observed_score


def teacher_label(teacher_id: str) -> str:
    number = int(teacher_id.split("-")[1])
    return f"Teacher {number:02d}"


def class_size_band(size: int) -> str:
    if size <= 6:
        return "micro"
    if 7 <= size <= 12:
        return "small"
    if 13 <= size <= 18:
        return "standard"
    return "large"


def section_growth_effect(section_index: int) -> float:
    pattern = (-0.30, -0.20, -0.10, 0.00, 0.10, 0.20, 0.30)
    return pattern[(section_index - 1) % len(pattern)]


def synthetic_student_names(idx: int) -> tuple[str, str]:
    first_name = FIRST_NAMES[(idx - 1) % len(FIRST_NAMES)]
    last_name = LAST_NAMES[((idx - 1) // len(FIRST_NAMES) + idx - 1) % len(LAST_NAMES)]
    return first_name, last_name


def build_student(idx: int, graduation_year: int, entry_school_year_offset: int, rng: random.Random) -> dict[str, Any]:
    first_name, last_name = synthetic_student_names(idx)
    attendance_category, beta_params = choose_attendance_category(rng)
    attendance_probability = rng.betavariate(*beta_params)
    graduation_suffix = f"{graduation_year % 100:02d}"
    exit_offset = graduation_year - (BASE_START_YEAR + 1)
    return {
        "student_key": f"SYN-SIS-{idx:06d}",
        "student_label": f"Synthetic Student {idx:03d}",
        "export_id": f"SYN-EXP-{idx:06d}",
        "login_id": f"synthetic{idx:03d}",
        "email": f"{first_name[0].lower()}{last_name.lower()}{graduation_suffix}@{SYNTHETIC_EMAIL_DOMAIN}",
        "canvas_gradebook_section": CANVAS_SECTIONS[(idx - 1) % len(CANVAS_SECTIONS)],
        "graduation_year": graduation_year,
        "graduation_year_suffix": graduation_suffix,
        "cohort_label": f"class_of_{graduation_year}",
        "entry_school_year_offset": entry_school_year_offset,
        "entry_school_year": school_year_for_offset(entry_school_year_offset),
        "graduation_school_year_offset": exit_offset,
        "graduation_school_year": school_year_for_offset(exit_offset) if 0 <= exit_offset < SCHOOL_YEAR_COUNT else None,
        "attendance_category": attendance_category,
        "attendance_probability": round(attendance_probability, 4),
    }


def generate_students() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    students: list[dict[str, Any]] = []
    next_idx = 1

    for grade_level in INITIAL_GRADE_LEVEL_SEQUENCE:
        graduation_year = school_year_end(0) + (12 - grade_level)
        students.append(build_student(next_idx, graduation_year, 0, rng))
        next_idx += 1

    for offset in range(1, SCHOOL_YEAR_COUNT):
        graduating_count = sum(
            1
            for student in students
            if active_in_year(student, offset - 1)
            and grade_for_graduation_year(int(student["graduation_year"]), offset - 1) == 12
        )
        freshman_graduation_year = school_year_end(offset) + 3
        for _ in range(graduating_count):
            students.append(build_student(next_idx, freshman_graduation_year, offset, rng))
            next_idx += 1

    return students


def active_students_for_year(students: list[dict[str, Any]], offset: int) -> list[dict[str, Any]]:
    return [student for student in students if active_in_year(student, offset)]


def apportion_counts(source_counts: dict[str, int], target_count: int) -> dict[str, int]:
    source_total = sum(source_counts.values())
    raw_allocations = {
        course_id: (count / source_total) * target_count
        for course_id, count in source_counts.items()
    }
    allocations = {course_id: int(math.floor(value)) for course_id, value in raw_allocations.items()}
    remaining = target_count - sum(allocations.values())
    remainders = sorted(raw_allocations.items(), key=lambda item: item[1] - math.floor(item[1]), reverse=True)
    for course_id, _value in remainders[:remaining]:
        allocations[course_id] += 1
    return allocations


def assign_initial_courses(students: list[dict[str, Any]]) -> dict[str, str]:
    rng = random.Random(SEED + 31)
    assignments: dict[str, str] = {}
    students_by_grade: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for student in students:
        grade = grade_for_graduation_year(int(student["graduation_year"]), 0)
        students_by_grade[grade].append(student)

    for grade, course_counts in INITIAL_GRADE_COURSE_COUNTS.items():
        grade_students = students_by_grade[grade]
        if len(grade_students) != sum(course_counts.values()):
            raise ValueError(f"Grade {grade} initial course counts do not match active students.")
        rng.shuffle(grade_students)
        cursor = 0
        for course_id, count in course_counts.items():
            for student in grade_students[cursor : cursor + count]:
                assignments[student["student_key"]] = course_id
            cursor += count
    return assignments


def assign_new_freshman_courses(students: list[dict[str, Any]], rng: random.Random) -> dict[str, str]:
    assignments: dict[str, str] = {}
    course_counts = apportion_counts(INITIAL_GRADE_COURSE_COUNTS[9], len(students))
    shuffled = list(students)
    rng.shuffle(shuffled)
    cursor = 0
    for course_id, count in course_counts.items():
        for student in shuffled[cursor : cursor + count]:
            assignments[student["student_key"]] = course_id
        cursor += count
    return assignments


def promote_course(previous_course_id: str, readiness: float | None, rng: random.Random) -> str:
    readiness_value = readiness if readiness is not None else 52.0 + rng.gauss(0, 8.0)
    if previous_course_id == "MATH-ALG1":
        return "MATH-GEOM"
    if previous_course_id == "MATH-GEOM":
        return "MATH-ALG2-H" if readiness_value >= 58.0 else "MATH-ALG2"
    if previous_course_id == "MATH-ALG2":
        return "MATH-PRECALC"
    if previous_course_id == "MATH-ALG2-H":
        return "MATH-AP-PRECALC"
    if previous_course_id == "MATH-PRECALC":
        return "MATH-AP-CALC-AB"
    if previous_course_id == "MATH-AP-PRECALC":
        return "MATH-AP-CALC-BC" if readiness_value >= 78.0 else "MATH-AP-CALC-AB"
    if previous_course_id == "MATH-AP-CALC-AB":
        return "MATH-AP-CALC-BC"
    return "MATH-BEYOND-CORE"


def split_section_sizes(student_count: int) -> list[int]:
    if student_count <= 0:
        return []
    section_count = max(1, math.ceil(student_count / 14))
    base_size = student_count // section_count
    extras = student_count % section_count
    return [base_size + (1 if idx < extras else 0) for idx in range(section_count)]


def choose_teacher(course_id: str, teacher_loads: dict[str, int]) -> str:
    preferred = TEACHER_COURSE_PREFERENCES[course_id]
    under_target = [teacher_id for teacher_id in preferred if teacher_loads[teacher_id] < 5]
    if under_target:
        return min(under_target, key=lambda teacher_id: (teacher_loads[teacher_id], preferred.index(teacher_id)))
    under_rare_load = [teacher_id for teacher_id in preferred if teacher_loads[teacher_id] < 6]
    if under_rare_load:
        return min(under_rare_load, key=lambda teacher_id: (teacher_loads[teacher_id], preferred.index(teacher_id)))
    return min(teacher_loads, key=lambda teacher_id: (teacher_loads[teacher_id], teacher_id))


def build_course_rows() -> list[dict[str, str | int | bool]]:
    return [dict(course) for course in COURSES]


def build_teacher_rows() -> list[dict[str, str | int | float]]:
    rows = []
    for offset in range(SCHOOL_YEAR_COUNT):
        school_year = school_year_for_offset(offset)
        for teacher_id, effect in sorted(TEACHER_GROWTH_EFFECTS.items()):
            rows.append(
                {
                    "school_year": school_year,
                    "teacher_id": teacher_id,
                    "teacher_label": teacher_label(teacher_id),
                    "target_section_load": 5,
                    "teacher_growth_effect": effect,
                }
            )
    return rows


def build_sections_for_year(
    school_year_offset: int,
    course_assignments: dict[str, str],
) -> list[dict[str, str | int | float]]:
    school_year = school_year_for_offset(school_year_offset)
    course_lookup = {course["course_id"]: course for course in COURSES}
    course_counts = Counter(course_assignments.values())
    teacher_loads = {teacher_id: 0 for teacher_id in TEACHER_GROWTH_EFFECTS}
    rows: list[dict[str, str | int | float]] = []
    local_section_index = 1

    for course in sorted(COURSES, key=lambda row: (row["sequence_order"], row["course_id"])):
        course_id = str(course["course_id"])
        for section_size in split_section_sizes(course_counts[course_id]):
            teacher_id = choose_teacher(course_id, teacher_loads)
            teacher_loads[teacher_id] += 1
            section_id = f"Y{school_year_offset:02d}-SEC-{local_section_index:03d}"
            band = class_size_band(section_size)
            rows.append(
                {
                    "school_year": school_year,
                    "school_year_offset": school_year_offset,
                    "section_id": section_id,
                    "course_id": course_id,
                    "section_label": f"{course_lookup[course_id]['course_name']} - Synthetic Section {school_year_offset + 1:02d}-{local_section_index:02d}",
                    "teacher_id": teacher_id,
                    "teacher_label": teacher_label(teacher_id),
                    "period_label": f"Period {((teacher_loads[teacher_id] - 1) % 6) + 1}",
                    "target_enrollment": section_size,
                    "max_capacity": {"micro": 6, "small": 12, "standard": 18, "large": 24}[band],
                    "class_size_band": band,
                    "section_growth_effect": section_growth_effect(local_section_index),
                    "teacher_growth_effect": TEACHER_GROWTH_EFFECTS[teacher_id],
                }
            )
            local_section_index += 1
    return rows


def build_enrollments_for_year(
    school_year_offset: int,
    active_students: list[dict[str, Any]],
    course_assignments: dict[str, str],
    section_rows: list[dict[str, str | int | float]],
) -> list[dict[str, str | int]]:
    rng = random.Random(SEED + 43 + school_year_offset)
    school_year = school_year_for_offset(school_year_offset)
    students_by_course: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for student in active_students:
        students_by_course[course_assignments[student["student_key"]]].append(student)

    sections_by_course: dict[str, list[dict[str, str | int | float]]] = defaultdict(list)
    for section in section_rows:
        sections_by_course[str(section["course_id"])].append(section)

    enrollment_rows = []
    for course_id, students in sorted(students_by_course.items()):
        sections = sections_by_course[course_id]
        target_total = sum(int(section["target_enrollment"]) for section in sections)
        if target_total != len(students):
            raise ValueError(f"{school_year} {course_id} has {len(students)} students but section targets sum to {target_total}.")
        rng.shuffle(students)
        cursor = 0
        for section in sections:
            section_size = int(section["target_enrollment"])
            for student in students[cursor : cursor + section_size]:
                enrollment_rows.append(
                    {
                        "school_year": school_year,
                        "school_year_offset": school_year_offset,
                        "Student": student["student_label"],
                        "SIS User ID": student["student_key"],
                        "grade_level": grade_for_graduation_year(int(student["graduation_year"]), school_year_offset),
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
        school_year_offset = (idx - 1) // 2
        assessment_window = "beginning_of_year" if idx % 2 == 1 else "end_of_year"
        transition_type = "initialize_readiness" if idx == 1 else "school_year_growth" if idx % 2 == 0 else "summer_atrophy"
        assignments.append(
            {
                "assignment_label": assignment_label_for_sequence(idx),
                "sequence_index": idx,
                "school_year": school_year_for_offset(school_year_offset),
                "school_year_offset": school_year_offset,
                "assessment_window": assessment_window,
                "transition_type": transition_type,
                "population_status": "populated",
            }
        )
    return assignments


def assessment_context_from_enrollment(
    assignment: dict[str, str | int],
    enrollment: dict[str, str | int],
    course_rows: list[dict[str, str | int | bool]],
    section_rows: list[dict[str, str | int | float]],
) -> AssessmentContext:
    course_by_id = {str(course["course_id"]): course for course in course_rows}
    section_by_key = {
        (str(section["school_year"]), str(section["section_id"])): section
        for section in section_rows
    }
    school_year = str(enrollment["school_year"])
    section = section_by_key[(school_year, str(enrollment["section_id"]))]
    course = course_by_id[str(enrollment["course_id"])]
    return AssessmentContext(
        school_year=school_year,
        school_year_offset=int(assignment["school_year_offset"]),
        assignment_label=str(assignment["assignment_label"]),
        sequence_index=int(assignment["sequence_index"]),
        assessment_window=str(assignment["assessment_window"]),
        expected_transition_type=str(assignment["transition_type"]),
        grade_level=int(enrollment["grade_level"]),
        course_id=str(enrollment["course_id"]),
        course_track=str(course["track"]),
        section_id=str(enrollment["section_id"]),
        teacher_id=str(enrollment["teacher_id"]),
        instructor_effect=float(section["teacher_growth_effect"]),
        section_effect=float(section["section_growth_effect"]),
    )


def format_score(value: float | int | str | None) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value
    return f"{value:g}"


def build_state_and_artifacts() -> dict[str, Any]:
    students = generate_students()
    course_rows = build_course_rows()
    teacher_rows = build_teacher_rows()
    assignments = build_assignment_definitions()

    runtime: dict[str, dict[str, float | None]] = {
        student["student_key"]: {"latent_readiness": None, "observed_readiness": None, "last_present_score": None}
        for student in students
    }
    assignment_scores_by_student: dict[str, dict[str, float]] = defaultdict(dict)
    assessment_history_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    previous_course_by_student: dict[str, str] = {}
    all_sections: list[dict[str, str | int | float]] = []
    all_enrollments: list[dict[str, str | int]] = []
    all_assessment_scores: list[dict[str, str | int | float | bool | None]] = []
    school_year_records: list[dict[str, Any]] = []
    rng = random.Random(SEED + 59)

    for offset in range(SCHOOL_YEAR_COUNT):
        school_year = school_year_for_offset(offset)
        active_students = active_students_for_year(students, offset)
        if len(active_students) != ACTIVE_STUDENT_COUNT:
            raise ValueError(f"{school_year} has {len(active_students)} active students, expected {ACTIVE_STUDENT_COUNT}.")

        if offset == 0:
            course_assignments = assign_initial_courses(active_students)
        else:
            year_rng = random.Random(SEED + 71 + offset)
            new_students = [student for student in active_students if int(student["entry_school_year_offset"]) == offset]
            continuing_students = [student for student in active_students if int(student["entry_school_year_offset"]) < offset]
            course_assignments = assign_new_freshman_courses(new_students, year_rng)
            for student in continuing_students:
                previous_course = previous_course_by_student[student["student_key"]]
                latent_readiness = runtime[student["student_key"]]["latent_readiness"]
                course_assignments[student["student_key"]] = promote_course(previous_course, latent_readiness, year_rng)

        section_rows = build_sections_for_year(offset, course_assignments)
        enrollment_rows = build_enrollments_for_year(offset, active_students, course_assignments, section_rows)
        all_sections.extend(section_rows)
        all_enrollments.extend(enrollment_rows)

        enrollment_by_student = {str(enrollment["SIS User ID"]): enrollment for enrollment in enrollment_rows}
        year_assignments = [assignment for assignment in assignments if int(assignment["school_year_offset"]) == offset]
        for assignment in year_assignments:
            for student in sorted(active_students, key=lambda row: str(row["student_key"])):
                student_key = str(student["student_key"])
                enrollment = enrollment_by_student[student_key]
                context = assessment_context_from_enrollment(assignment, enrollment, course_rows, section_rows)
                result, next_latent_readiness, next_observed_readiness, next_present_score = generate_assessment_score(
                    rng,
                    student,
                    runtime[student_key]["latent_readiness"],
                    runtime[student_key]["observed_readiness"],
                    runtime[student_key]["last_present_score"],
                    context,
                )
                runtime[student_key]["latent_readiness"] = next_latent_readiness
                runtime[student_key]["observed_readiness"] = next_observed_readiness
                runtime[student_key]["last_present_score"] = next_present_score
                assignment_scores_by_student[student_key][context.assignment_label] = result.observed_score

                score_row = {
                    "school_year": context.school_year,
                    "school_year_offset": context.school_year_offset,
                    "assignment_label": context.assignment_label,
                    "sequence_index": context.sequence_index,
                    "assessment_window": context.assessment_window,
                    "expected_transition_type": context.expected_transition_type,
                    "actual_transition_type": result.actual_transition_type,
                    "generation_mode": result.generation_mode,
                    "sis_user_id": student_key,
                    "student_label": student["student_label"],
                    "grade_level": context.grade_level,
                    "course_id": context.course_id,
                    "course_track": context.course_track,
                    "section_id": context.section_id,
                    "teacher_id": context.teacher_id,
                    "attendance_category": student["attendance_category"],
                    "attendance_probability": student["attendance_probability"],
                    "present": result.present,
                    "observed_score": result.observed_score,
                    "potential_score": result.potential_score,
                    "posterior_readiness_after": result.posterior_readiness_after,
                    "growth_delta": result.growth_delta,
                    "latent_transition_type": result.latent_transition_type,
                    "latent_readiness_before": result.latent_readiness_before,
                    "latent_readiness_after": result.latent_readiness_after,
                    "latent_transition_delta": result.latent_transition_delta,
                    "academic_profile_status": result.academic_profile_status,
                }
                all_assessment_scores.append(score_row)
                assessment_history_by_student[student_key].append(score_row)

        previous_course_by_student = {
            str(enrollment["SIS User ID"]): str(enrollment["course_id"])
            for enrollment in enrollment_rows
        }

        grade_counts = Counter(int(enrollment["grade_level"]) for enrollment in enrollment_rows)
        course_counts = Counter(str(enrollment["course_id"]) for enrollment in enrollment_rows)
        school_year_records.append(
            {
                "school_year": school_year,
                "school_year_offset": offset,
                "beginning_assignment_label": year_assignments[0]["assignment_label"],
                "end_assignment_label": year_assignments[1]["assignment_label"],
                "active_student_count": len(active_students),
                "new_freshman_count": sum(1 for student in active_students if int(student["entry_school_year_offset"]) == offset and offset > 0),
                "graduating_senior_count": grade_counts[12],
                "grade_counts": dict(sorted(grade_counts.items())),
                "course_counts": dict(sorted(course_counts.items())),
                "section_count": len(section_rows),
            }
        )

    rendered_students = []
    for student in students:
        student_key = str(student["student_key"])
        active_years = [
            {
                "school_year": school_year_for_offset(offset),
                "school_year_offset": offset,
                "grade_level": grade_for_graduation_year(int(student["graduation_year"]), offset),
            }
            for offset in range(SCHOOL_YEAR_COUNT)
            if active_in_year(student, offset)
        ]
        latest_history = assessment_history_by_student[student_key][-1] if assessment_history_by_student[student_key] else {}
        rendered_students.append(
            {
                **student,
                "active_years": active_years,
                "assignment_scores": dict(sorted(assignment_scores_by_student[student_key].items())),
                "assessment_profile": {
                    "attendance_category": student["attendance_category"],
                    "attendance_probability": student["attendance_probability"],
                    "latest_academic_profile_status": latest_history.get("academic_profile_status", "not_active_in_simulation"),
                    "latest_posterior_readiness": runtime[student_key]["observed_readiness"],
                    "latest_latent_readiness": runtime[student_key]["latent_readiness"],
                    "latest_present_score": runtime[student_key]["last_present_score"],
                },
                "assessment_history": assessment_history_by_student[student_key],
            }
        )

    canvas_profile_artifacts = []
    for record in school_year_records:
        year = record["school_year"]
        for course_id in record["course_counts"]:
            canvas_profile_artifacts.append(f"canvas_course_profiles/{year}/{course_id}.json")

    assessment_shell_artifacts = [
        f"assessment_shells/{record['school_year']}/synthetic_asma_gradebook.csv"
        for record in school_year_records
    ]

    return {
        "schema_version": "synthetic_math_department_state_v3",
        "random_seed": SEED,
        "base_school_year": school_year_for_offset(0),
        "school_year_count": SCHOOL_YEAR_COUNT,
        "active_student_count_per_year": ACTIVE_STUDENT_COUNT,
        "longitudinal_model": {
            "model_version": LONGITUDINAL_MODEL_VERSION,
            "generated_assignments": [assignment["assignment_label"] for assignment in assignments],
            "implemented_transition_types": ["initialize_readiness", "school_year_growth", "summer_atrophy", "absent_no_update"],
            "implemented_latent_transition_types": ["initialize_latent_readiness", "school_year_growth", "summer_atrophy"],
            "grade_prior_shift_per_grade": GRADE_PRIOR_SHIFT_PER_GRADE,
            "readiness_prior_sd": READINESS_PRIOR_SD,
            "measurement_error_sd": MEASUREMENT_ERROR_SD,
            "growth_noise_sd": GROWTH_NOISE_SD,
            "observation_noise_sd": OBSERVATION_NOISE_SD,
        },
        "school_years": school_year_records,
        "students": sorted(rendered_students, key=lambda row: str(row["student_key"])),
        "teachers": teacher_rows,
        "courses": course_rows,
        "sections": all_sections,
        "enrollments": all_enrollments,
        "assessment_scores": all_assessment_scores,
        "assessment_shells": [
            {
                "assessment_shell_id": f"ASMA-ALL-MATH-{record['school_year']}",
                "assessment_shell_label": "All School Math Assessment",
                "school_year": record["school_year"],
                "school_year_offset": record["school_year_offset"],
                "source_system": "synthetic_canvas",
                "join_key": "email",
                "raw_gradebook_artifact": f"assessment_shells/{record['school_year']}/synthetic_asma_gradebook.csv",
                "student_count": record["active_student_count"],
                "assignment_labels": [record["beginning_assignment_label"], record["end_assignment_label"]],
            }
            for record in school_year_records
        ],
        "assignments": assignments,
        "derived_artifacts": [
            "synthetic_school_state.json",
            "synthetic_asma_gradebook.csv",
            "synthetic_assessment_scores_long.csv",
            "synthetic_math_courses.csv",
            "synthetic_math_sections.csv",
            "synthetic_math_enrollments.csv",
            *assessment_shell_artifacts,
            *canvas_profile_artifacts,
        ],
    }


def render_combined_gradebook_rows_from_state(state: dict[str, Any]) -> list[dict[str, str]]:
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


def render_yearly_gradebook_rows_from_state(state: dict[str, Any], school_year: str) -> tuple[list[str], list[dict[str, str]]]:
    year_record = next(record for record in state["school_years"] if record["school_year"] == school_year)
    assignment_labels = [year_record["beginning_assignment_label"], year_record["end_assignment_label"]]
    active_student_ids = {
        enrollment["SIS User ID"]
        for enrollment in state["enrollments"]
        if enrollment["school_year"] == school_year
    }
    rows = []
    for student in state["students"]:
        if student["student_key"] not in active_student_ids:
            continue
        rows.append(
            {
                "Student": student["student_label"],
                "ID": student["export_id"],
                "SIS User ID": student["student_key"],
                "SIS Login ID": student["login_id"],
                "Email": student["email"],
                "Section": student["canvas_gradebook_section"],
                **{label: format_score(student["assignment_scores"].get(label)) for label in assignment_labels},
            }
        )
    fieldnames = ["Student", "ID", "SIS User ID", "SIS Login ID", "Email", "Section", *assignment_labels]
    return fieldnames, sorted(rows, key=lambda row: row["SIS User ID"])


def render_canvas_course_profiles_from_state(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    students_by_id = {student["student_key"]: student for student in state["students"]}
    courses_by_id = {course["course_id"]: course for course in state["courses"]}

    sections_by_year_course: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for section in state["sections"]:
        sections_by_year_course[(section["school_year"], section["course_id"])].append(section)

    enrollments_by_year_section: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for enrollment in state["enrollments"]:
        enrollments_by_year_section[(enrollment["school_year"], enrollment["section_id"])].append(enrollment)

    profiles = {}
    for (school_year, course_id), sections in sorted(sections_by_year_course.items()):
        course = courses_by_id[course_id]
        course_sections = []
        for section in sorted(sections, key=lambda row: row["section_id"]):
            section_students = []
            for enrollment in sorted(enrollments_by_year_section[(school_year, section["section_id"])], key=lambda row: row["SIS User ID"]):
                student = students_by_id[enrollment["SIS User ID"]]
                section_students.append(
                    {
                        "Student": student["student_label"],
                        "SIS User ID": student["student_key"],
                        "Email": student["email"],
                        "grade_level": enrollment["grade_level"],
                        "enrollment_status": enrollment["enrollment_status"],
                    }
                )

            course_sections.append(
                {
                    "section_id": section["section_id"],
                    "section_label": section["section_label"],
                    "period_label": section["period_label"],
                    "teacher": {
                        "teacher_id": section["teacher_id"],
                        "teacher_label": section["teacher_label"],
                    },
                    "students": section_students,
                }
            )

        profiles[f"{school_year}/{course_id}.json"] = {
            "canvas_course_id": f"SYN-CANVAS-{course_id}-{school_year}",
            "course_id": course_id,
            "course_name": course["course_name"],
            "track": course["track"],
            "school_year": school_year,
            "source_system": "synthetic_canvas",
            "sections": course_sections,
        }

    return profiles


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp_path = Path(file.name)
            writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        temp_path.replace(path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp_path = Path(file.name)
            json.dump(payload, file, indent=2, sort_keys=True)
            file.write("\n")
        temp_path.replace(path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def write_canvas_course_profiles(path: Path, profiles: dict[str, dict[str, Any]]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    expected_paths = set()
    for relative_path, profile in sorted(profiles.items()):
        output_path = path / relative_path
        expected_paths.add(output_path)
        write_json(output_path, profile)

    for stale_path in sorted(path.rglob("*.json")):
        if stale_path not in expected_paths:
            stale_path.unlink()
    prune_empty_directories(path)


def write_yearly_assessment_shells(state: dict[str, Any]) -> None:
    ASSESSMENT_SHELLS_DIR.mkdir(parents=True, exist_ok=True)
    expected_paths = set()
    for record in state["school_years"]:
        fieldnames, rows = render_yearly_gradebook_rows_from_state(state, record["school_year"])
        output_path = ASSESSMENT_SHELLS_DIR / record["school_year"] / "synthetic_asma_gradebook.csv"
        expected_paths.add(output_path)
        write_csv(output_path, fieldnames, rows)

    for stale_path in sorted(ASSESSMENT_SHELLS_DIR.rglob("*.csv")):
        if stale_path not in expected_paths:
            stale_path.unlink()
    prune_empty_directories(ASSESSMENT_SHELLS_DIR)


def prune_empty_directories(path: Path) -> None:
    for directory in sorted((candidate for candidate in path.rglob("*") if candidate.is_dir()), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def main() -> None:
    state = build_state_and_artifacts()
    gradebook_rows = render_combined_gradebook_rows_from_state(state)
    canvas_course_profiles = render_canvas_course_profiles_from_state(state)

    write_json(STATE_PATH, state)
    write_canvas_course_profiles(CANVAS_COURSE_PROFILES_DIR, canvas_course_profiles)
    write_yearly_assessment_shells(state)
    write_csv(
        GRADEBOOK_PATH,
        ["Student", "ID", "SIS User ID", "SIS Login ID", "Email", "Section", *[assignment_label_for_sequence(idx) for idx in range(1, ASSIGNMENT_COUNT + 1)]],
        gradebook_rows,
    )
    write_csv(COURSES_PATH, ["course_id", "course_name", "track", "sequence_order", "current_year_eligible"], state["courses"])
    write_csv(
        SECTIONS_PATH,
        [
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
        ],
        state["sections"],
    )
    write_csv(
        ENROLLMENTS_PATH,
        ["school_year", "school_year_offset", "Student", "SIS User ID", "grade_level", "course_id", "section_id", "teacher_id", "enrollment_status"],
        state["enrollments"],
    )
    write_csv(
        ASSESSMENT_LONG_PATH,
        [
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
        ],
        state["assessment_scores"],
    )


if __name__ == "__main__":
    main()
