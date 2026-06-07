# Synthetic Math Department

A privacy-preserving synthetic education data engine that simulates a high-school math department for assessment analytics, dashboard development, and learning-systems prototyping.

This repository is designed to solve a practical portfolio problem: how to demonstrate education analytics infrastructure without publishing protected student data, raw LMS exports, real gradebooks, teacher names, section labels, or school-private records.

It is not just a fake CSV generator. The project creates a coherent synthetic department system with students, teachers, courses, sections, enrollments, assessment scores, attendance/non-participation behavior, Canvas-style course artifacts, and validation checks.

## What This Project Demonstrates

- Synthetic education data generation for public-safe analytics demos
- Nested education data structure: students, sections, courses, teachers, and enrollments
- Canvas-style all-school math assessment gradebook generation
- Assessment score simulation with attendance/non-participation modeled separately from academic performance
- Course-track, teacher, section, growth, measurement-error, observation-noise, and regression-to-the-mean effects
- Bayesian-style readiness updates for reusable longitudinal score generation
- Grade-level calibration diagnostics for longitudinal modeling
- Canonical state object generation with reproducible CSV and JSON exports
- Validation of counts, schema, enrollment consistency, score bounds, assignment population policy, Canvas-style profiles, and public-safety constraints

## Statistical Design

The generator separates the department structure from the assessment measurement process.

```text
synthetic students, teachers, courses, sections, enrollments
-> assessment context by grade, course, track, teacher, and section
-> attendance / non-participation draw
-> latent readiness and observed assessment score
-> validation-ready public artifacts
```

`Assignment 01` is a beginning-of-year assessment. Present-student scores are drawn from grade-specific public-safe calibration anchors, then attendance is modeled separately. Under this design, an observed zero means non-participation, not academic evidence.

`Assignment 02` is the first application of the reusable longitudinal score engine. The engine updates academic readiness from prior evidence when appropriate, applies school-year growth, adds course/track and teacher/section effects, includes regression-to-the-mean behavior, and separates growth noise from assessment observation noise.

If a student is absent for an assessment window, the observed score is `0` and academic readiness is not updated.

## Workflow

```text
synthetic math department state
-> synthetic ASMA gradebook
-> synthetic course, section, and enrollment exports
-> validation
-> downstream assessment analysis
```

The canonical source of truth is:

```text
data/synthetic/synthetic_school_state.json
```

Downstream CSV artifacts are rendered from that state:

```text
data/synthetic/synthetic_asma_gradebook.csv
data/synthetic/synthetic_math_courses.csv
data/synthetic/synthetic_math_sections.csv
data/synthetic/synthetic_math_enrollments.csv
```

The generator also renders synthetic Canvas-style course profiles:

```text
data/synthetic/canvas_course_profiles/
```

## What To Inspect First

- [docs/methodology.md](docs/methodology.md) explains the data-generating process, Assignment 01 score generation, the longitudinal score engine, Canvas-style artifacts, and validation checks.
- [data/synthetic/synthetic_school_state.json](data/synthetic/synthetic_school_state.json) is the canonical state object used to render downstream artifacts.
- [data/synthetic/synthetic_asma_gradebook.csv](data/synthetic/synthetic_asma_gradebook.csv) is the public-safe all-school math assessment gradebook.
- [scripts/generate_synthetic_math_department.py](scripts/generate_synthetic_math_department.py) contains the simulation logic.
- [scripts/validate_synthetic_math_department.py](scripts/validate_synthetic_math_department.py) checks artifact shape, coherence, score policy, and public-safety boundaries.
- [reports/grade-level-calibration/grade-level-calibration-report.md](reports/grade-level-calibration/grade-level-calibration-report.md) shows the aggregate calibration diagnostics used to support weak grade-level priors.

## Generate And Validate

```bash
make all
```

Or run the steps separately:

```bash
make generate
make validate
```

The project uses only the Python standard library.

Optional grade-level calibration diagnostics can be generated from a private gradebook path:

```bash
SOURCE_GRADEBOOK=/path/to/private/gradebook.csv make calibrate-grade-level
```

The calibration target writes public-safe aggregate diagnostics only. It does not write source rows, identifiers, emails, section labels, or private paths to public outputs.

## Relationship To Assessment Intelligence

This repository is the synthetic data foundation.

The downstream `assessment-intelligence` project is responsible for the visual analytics and reporting layer: dashboards, distribution checks, growth diagnostics, decision-support reports, and leadership-facing interpretation.

```text
synthetic-math-department -> data generation and validation
assessment-intelligence -> analytics, dashboards, diagnostics, and reporting
```

## Public Safety

This repository is designed to be public-safe from the first commit. It contains synthetic data and generalized methodology only.

Do not commit:

- real students, emails, IDs, or rosters
- raw LMS exports
- private assessment artifacts
- private teacher names
- internal section labels
- school-private paths
- private calibration/debug files

See [docs/public-safety.md](docs/public-safety.md) for the release boundary.

## Current Status

Current version is an active simulation engine for one baseline school year, not a finished multi-year longitudinal system.

It generates a baseline 2025-2026 synthetic math department with:

- 287 synthetic students
- 5 synthetic teachers
- 9 math course entries
- 25 sections
- 287 active enrollments
- 8 synthetic Canvas course JSON profiles
- 14 assessment assignment fields
- `Assignment 01` populated as beginning-of-year assessment
- `Assignment 02` populated as the first reusable-engine end-of-year transition

Assignments 03-14 are intentionally blank until later longitudinal transitions are implemented and validated.

## Portfolio Fit

This project is strongest for assessment analyst, education data analyst, institutional research, learning analytics, and edtech data/product roles. It demonstrates statistical simulation, privacy-aware data design, domain modeling, validation workflow, and analytics infrastructure.

For a more analysis-facing view of the same synthetic data ecosystem, see the downstream `assessment-intelligence` project.
