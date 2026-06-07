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
data/synthetic/synthetic_math_courses.csv
data/synthetic/synthetic_math_sections.csv
data/synthetic/synthetic_math_enrollments.csv
data/synthetic/canvas_course_profiles/
```

The gradebook contains synthetic Canvas-style student identifiers and 14 generic assignment fields. `Assignment 01` is populated as the beginning-of-year assessment, and `Assignment 02` is populated as the end-of-year assessment. Assignments 03-14 remain scaffolded for later longitudinal transitions.

The course, section, and enrollment CSVs provide the math department context needed for downstream analysis.

The course profile directory contains one JSON file per current-year eligible math course. Each JSON profile includes course metadata, sections, fake teacher metadata, and enrolled synthetic students.

## Join Model

The intended join key is the synthetic student email:

```text
Email
```

The `SIS User ID` field is also stable and unique. Downstream analysis can use either key, but email mirrors the practical Canvas-course join workflow.

## Course JSON Profiles

Synthetic Canvas course JSON profiles are rendered from the canonical state. They function as year-specific course shells for the workflow simulation.

Current shape:

```text
synthetic_school_state.json
-> synthetic ASMA gradebook CSV
-> synthetic Canvas math course JSON profiles
```

Future enriched analysis shape:

```text
synthetic_school_state.json
-> synthetic ASMA gradebook CSV
-> synthetic Canvas math course JSON profiles
-> enriched SDA.csv
```

Each course JSON profile should include:

- course metadata
- teacher metadata
- sections
- enrolled synthetic students
- synthetic email join keys
- enrollment status

The JSON profiles should be downstream renderings of the canonical state, not separate sources of truth.

## Downstream Analysis

The `assessment-intelligence` project should consume the generated artifacts and perform the analysis/reporting work:

```text
synthetic-education-data -> generates public-safe environment and data
assessment-intelligence -> analyzes, reports, and dashboards the data
```
