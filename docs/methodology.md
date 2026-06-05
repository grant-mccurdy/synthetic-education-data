# Synthetic Math Department Methodology

## Purpose

This project generates a public-safe synthetic math department environment. The output is intended to behave like a plausible math department data system without exposing real students, real course rosters, real LMS exports, or private institutional records.

The generator is designed around one canonical state object:

```text
data/synthetic/synthetic_school_state.json
```

CSV outputs are rendered from that state rather than generated as unrelated files.

## Baseline Environment

The current baseline simulates one school year:

```text
2025-2026
```

The v1 environment includes:

- 287 synthetic students
- 5 synthetic teachers
- 9 course entries
- 25 sections
- one active math enrollment per student
- 14 all-school math assessment assignment fields

The baseline is intentionally a compact math department rather than a full-school simulation.

## Course Catalog

The v1 course catalog focuses on the core high-school math sequence:

| Course ID | Course | Track |
| --- | --- | --- |
| `MATH-ALG1` | Algebra 1 | regular |
| `MATH-GEOM` | Geometry | regular |
| `MATH-ALG2` | Algebra 2 | regular |
| `MATH-ALG2-H` | Honors Algebra 2 | honors |
| `MATH-PRECALC` | Precalculus | regular |
| `MATH-AP-PRECALC` | AP Precalculus | ap |
| `MATH-AP-CALC-AB` | AP Calculus AB | ap |
| `MATH-AP-CALC-BC` | AP Calculus BC | ap |
| `MATH-BEYOND-CORE` | Beyond Core Math Sequence | beyond_core |

Geometry has no honors equivalent in v1. Honors/AP differentiation begins after Geometry. Statistics courses are excluded from the baseline.

## Assignment 01 Score Generation

`Assignment 01` models a beginning-of-year all-school math assessment.

The generator separates two processes:

```text
present-student academic score
attendance / non-participation outcome
```

The present-student academic score is drawn from grade-specific public-safe calibration anchors. These anchors are generalized distribution parameters, not raw private scores.

Then the generator draws attendance status:

| Attendance category | Student share | Distribution |
| --- | ---: | --- |
| `high` | 40% | `Beta(98, 2)` |
| `normal` | 50% | `Beta(92, 8)` |
| `at_risk` | 10% | `Beta(70, 30)` |

If the student is present, the observed `Assignment 01` score is the synthetic academic score. If the student is absent, the observed score is `0`.

Under this model, a zero on Assignment 01 means non-participation. It is not academic evidence.

## Assignment 02-14

Assignments 02-14 are intentionally present but blank in v1. They represent future longitudinal assessment windows:

| Assignment | Intended window |
| --- | --- |
| `Assignment 01` | beginning of year |
| `Assignment 02` | end of year |
| `Assignment 03` | beginning of next year |
| `Assignment 04` | end of next year |

The remaining assignments continue the beginning/end window pattern. They should be populated only after a longitudinal growth model is implemented.

## Canonical State

The state object contains:

- students
- teachers
- courses
- sections
- enrollments
- assessment shell metadata
- assignment definitions
- assignment scores currently populated

The state does not contain private calibration details, private paths, real identifiers, real emails, real teacher names, real section labels, raw source rows, or private LMS records.

## Validation

The validator checks:

- expected row counts
- one active math enrollment per student
- enrollments reference existing courses, sections, and teachers
- public CSV fields match the v1 schema
- `Assignment 01` is populated
- Assignments 02-14 are blank
- score bounds are valid
- banned private/source strings do not appear in public artifacts
