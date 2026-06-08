# Canvas Workflow Simulation

## Purpose

The synthetic math department model is designed to mirror a practical assessment workflow:

```text
all-school math assessment gradebook
+ math course enrollment context
-> analysis-ready assessment dataset
```

In a real workflow, the all-school assessment course might produce a Canvas-style gradebook, while individual math courses provide course, section, teacher, and roster context.

This repository generates the public-safe synthetic version of those artifacts.

## Current Artifacts

The current generator writes:

```text
data/synthetic/synthetic_asma_gradebook.csv
data/synthetic/synthetic_assessment_scores_long.csv
data/synthetic/synthetic_math_courses.csv
data/synthetic/synthetic_math_sections.csv
data/synthetic/synthetic_math_enrollments.csv
data/synthetic/assessment_shells/
data/synthetic/canvas_course_profiles/
```

The combined gradebook contains every synthetic student who is enrolled at any point in the seven-year simulation and 14 generic assignment fields. Assignment cells are populated only when a student is active during the corresponding school year.

The `assessment_shells/` directory contains one active-student ASMA gradebook per academic year. Each yearly shell includes the two assessment windows for that year.

The course, section, enrollment, and long assessment-score CSVs provide the math department context needed for downstream analysis.

The course profile directory contains year-scoped JSON files for active Canvas-like math courses:

```text
data/synthetic/canvas_course_profiles/2025-2026/MATH-ALG1.json
data/synthetic/canvas_course_profiles/2026-2027/MATH-ALG1.json
...
```

Each JSON profile includes course metadata, sections, fake teacher metadata, and active enrolled synthetic students for that school year.

## Join Model

The intended join key is the synthetic student email:

```text
Email
```

The `SIS User ID` field is also stable and unique. Downstream analysis can use either key, but email mirrors the practical Canvas-course join workflow.
Generated email identifiers use the reserved `schoolname.example` domain.

## Course JSON Profiles

Synthetic Canvas course JSON profiles are rendered from the canonical state. They function as year-specific course shells for the workflow simulation.

Current shape:

```text
synthetic_school_state.json
-> synthetic ASMA gradebook CSV
-> yearly synthetic ASMA gradebooks
-> year-scoped synthetic Canvas math course JSON profiles
```

Enriched analysis shape:

```text
synthetic_school_state.json
-> synthetic ASMA gradebook CSV
-> long assessment-score CSV
-> synthetic Canvas math course JSON profiles
-> normalized SQL tables
-> reconciled roster and assessment marts
-> enriched reporting extracts
```

Each course JSON profile should include:

- course metadata
- teacher metadata
- sections
- enrolled synthetic students
- synthetic email join keys
- enrollment status

The JSON profiles should be downstream renderings of the canonical state, not separate sources of truth.

## Canvas-To-SQL Extraction Simulation

The optional DuckDB warehouse treats the Canvas course JSON profiles as public-safe API-like payloads. The build script parses the course profiles and normalizes them into SQL tables:

```text
raw_canvas.courses
raw_canvas.sections
raw_canvas.enrollments
```

Those tables support a practical extraction protocol:

1. preserve source course-shell metadata
2. normalize nested section and roster records
3. retain stable LMS-style join keys, especially `SIS User ID` and `Email`
4. reconcile Canvas-derived rosters against canonical enrollment exports by school year
5. export dashboard-ready marts for downstream assessment analysis

This mirrors the real analytics problem of moving LMS data into a maintainable SQL layer before reporting.

## Downstream Analysis

The `assessment-intelligence` project should consume the generated artifacts and perform the analysis/reporting work:

```text
synthetic-education-data -> generates public-safe environment and data
assessment-intelligence -> analyzes, reports, and dashboards the data
```
