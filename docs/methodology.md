# Synthetic Math Department Methodology

## Purpose

This project generates a public-safe synthetic math department environment. The output is designed to behave like a plausible assessment and LMS data system without exposing real students, real course rosters, real LMS exports, private teacher names, internal section labels, or school-private records.

The generator is organized around one canonical state object:

```text
data/synthetic/synthetic_school_state.json
```

CSV and JSON artifacts are rendered from that state rather than generated as unrelated files.

## Simulation Horizon

The current simulation covers seven academic years:

```text
2025-2026 through 2031-2032
```

The model preserves a compact small-school math department scale:

- 287 active students per year
- 696 all-ever synthetic students across the full horizon
- 2,009 active student-year enrollments
- 5 synthetic teachers per school year
- 9 course entries
- 174 sections across the full horizon
- 14 standardized assessment windows

The churn model graduates seniors after each year and admits a replacement freshman cohort for the next year. This keeps the active department size stable while allowing realistic longitudinal entry and exit.

## Course Catalog

The course catalog focuses on the core high-school math sequence:

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

Geometry has no honors equivalent. Honors/AP differentiation begins after Geometry. Statistics courses are excluded from the baseline model. Students who complete AP Calculus BC before graduation may move into `MATH-BEYOND-CORE`.

## Student Churn And Placement

At the end of each academic year:

- grade 12 students graduate and become inactive
- grades 9-11 promote to the next grade
- a new grade 9 cohort is admitted
- freshman intake equals the prior year senior count

Course progression uses the prior course, current grade, and available readiness evidence:

```text
Algebra 1 -> Geometry
Geometry -> Algebra 2 or Honors Algebra 2
Algebra 2 -> Precalculus
Honors Algebra 2 -> AP Precalculus
Precalculus/AP Precalculus -> AP Calculus AB or AP Calculus BC
AP Calculus AB -> AP Calculus BC
AP Calculus BC -> Beyond Core Math Sequence
```

Teacher assignment favors stable subject-area ownership and target loads of five sections per teacher, with six sections allowed only when section counts require it.

## Assessment Score Generation

Assignments 01-14 represent standardized all-school math assessment windows:

| Assignments | School year | Windows |
| --- | --- | --- |
| `Assignment 01-02` | 2025-2026 | beginning/end |
| `Assignment 03-04` | 2026-2027 | beginning/end |
| `Assignment 05-06` | 2027-2028 | beginning/end |
| `Assignment 07-08` | 2028-2029 | beginning/end |
| `Assignment 09-10` | 2029-2030 | beginning/end |
| `Assignment 11-12` | 2030-2031 | beginning/end |
| `Assignment 13-14` | 2031-2032 | beginning/end |

The model separates two processes:

```text
present-student academic score
attendance / non-participation outcome
```

Present-student beginning scores are drawn from grade-specific public-safe calibration anchors. These anchors are generalized distribution parameters, not raw private scores.

Attendance is drawn independently from academic score:

| Attendance category | Student share | Distribution |
| --- | ---: | --- |
| `high` | 40% | `Beta(98, 2)` |
| `normal` | 50% | `Beta(92, 8)` |
| `at_risk` | 10% | `Beta(70, 30)` |

If a student is absent, the observed score is `0` and observed posterior readiness is not updated. If a student is present, the observed score is constrained to be greater than zero.

## Longitudinal Score Engine

The reusable score engine has this conceptual contract:

```text
student state
+ prior assessment evidence
+ school-year/course/section/teacher context
-> observed assessment score
-> updated academic readiness state when present
```

The engine includes:

- hidden latent readiness that evolves at every assessment window
- observed posterior readiness that updates only from present-score evidence
- weak grade-level prior shift
- course/track context
- synthetic teacher and section effects
- school-year growth
- summer atrophy between end-of-year and next beginning-of-year windows
- regression-to-the-mean behavior
- growth noise and observation noise
- Bayesian-style readiness updates after present scores

Students without prior latent state are initialized from a grade/window score distribution when they first become active in the assessment sequence. If they are absent, their observed score is `0` and their observed posterior readiness is not updated, but their hidden latent readiness still advances through school-year growth and summer atrophy.

The public gradebook contains observed scores only. The long assessment export includes additional synthetic latent-state fields for method inspection:

- `latent_transition_type`
- `latent_readiness_before`
- `latent_readiness_after`
- `latent_transition_delta`

## Artifacts

The combined longitudinal ASMA gradebook contains every synthetic student who appears at any point in the seven-year horizon:

```text
data/synthetic/synthetic_asma_gradebook.csv
```

Rows are all-ever students. Assignment cells are populated only for years when the student is actively enrolled; cells outside active years are blank.

Year-specific ASMA gradebooks contain only active students for that academic year:

```text
data/synthetic/assessment_shells/2025-2026/synthetic_asma_gradebook.csv
...
data/synthetic/assessment_shells/2031-2032/synthetic_asma_gradebook.csv
```

The preferred SQL/reporting input is the long score export:

```text
data/synthetic/synthetic_assessment_scores_long.csv
```

Canvas-style course profile JSONs are year-scoped:

```text
data/synthetic/canvas_course_profiles/2025-2026/MATH-ALG1.json
...
data/synthetic/canvas_course_profiles/2031-2032/MATH-AP-CALC-BC.json
```

Each JSON profile includes course metadata, sections, fake teacher metadata, active enrolled students, synthetic email join keys, and enrollment status.

## Canonical State

The state object contains:

- school years
- all-ever students
- teachers
- course catalog
- sections
- active student-year enrollments
- assessment shell metadata
- assignment definitions
- long assessment score records
- rendered artifact paths

The state does not contain private calibration details, private paths, real identifiers, real emails, real teacher names, real section labels, raw source rows, or private LMS records.

## Validation

The validator checks:

- seven school years
- 287 active students per year
- senior graduation and replacement freshman intake
- one active math enrollment per active student-year
- grade progression from 9 through 12
- combined and yearly gradebook schemas
- score bounds and non-participation-zero policy
- all 14 assessment windows populated for active student-year records
- attendance category shares and realized present-rate ordering
- positive average school-year growth and negative average summer atrophy
- latent readiness exists and remains bounded for every assessment window
- weak positive Assignment 01 grade-level score signal
- `Beyond Core Math Sequence` follows AP Calculus BC or a prior Beyond Core enrollment
- teacher section-load limits and section capacity bands
- Canvas course profiles reconciled to canonical enrollments by school year
- banned private/source strings do not appear in public artifacts
