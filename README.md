# Synthetic Math Department

Public-safe generator for a synthetic high-school math department data environment.

This repository generates coherent synthetic artifacts that can support downstream assessment analytics without publishing real students, grades, rosters, LMS exports, teacher names, section labels, or school-private records.

## What This Project Demonstrates

- Synthetic student population generation
- Math course, section, teacher, and enrollment simulation
- Canvas-style all-school math assessment gradebook generation
- Public-safe assessment score synthesis
- Attendance/non-participation modeling separate from academic performance
- Canonical state object generation
- Validation of data coherence and public-safety constraints

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

## Relationship To Assessment Intelligence

This repository generates a synthetic math department environment and data artifacts.

The downstream `assessment-intelligence` project can consume those artifacts to model growth, compare sections, build dashboards, write reports, and produce decision-support analysis.

```text
synthetic-math-department -> data generation
assessment-intelligence -> analysis and reporting
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

Version 1 generates a baseline 2025-2026 synthetic math department with:

- 287 synthetic students
- 5 synthetic teachers
- 9 math course entries
- 25 sections
- 287 active enrollments
- 14 assessment assignment fields
- only `Assignment 01` populated

Assignments 02-14 are intentionally blank until the longitudinal growth model is implemented.
