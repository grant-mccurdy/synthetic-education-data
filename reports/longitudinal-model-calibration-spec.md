# Longitudinal Model Calibration Spec

## Objective

Build the calibration layer for the synthetic math department longitudinal model.

The immediate purpose is to estimate how grade level should affect the prior for future assessment scores. The grade-level effect should be based on the private reference assessment data, validated through repeated sampling, and used as a weak prior shift rather than a dominant score predictor.

This model is implemented as a reusable next-assessment score engine. Assignment 02 was the first application, and the current generator now applies the same engine across Assignments 02-14.

Core method:

```text
real nonzero score pools by grade
-> grade-specific bootstrapped calibration distributions
-> repeated same-size validation samples
-> regression-output distributions
-> weak grade-level prior shift
```

## Source Data And Assumptions

Primary source:

```text
private Canvas gradebook path supplied at runtime
```

Source score field:

```text
column 9 / Unposted Final Score
```

Grade inference:

```text
infer grade from the last two digits of the student email graduation year
school year = 2025-2026
```

Grade mapping:

| Email year suffix | Inferred grade |
| --- | ---: |
| `29` | 9 |
| `28` | 10 |
| `27` | 11 |
| `26` | 12 |

Filtering rules:

- drop blank scores
- drop score `0` for present-score calibration
- treat score `0` as absence/admin outcome, not academic evidence
- do not copy source rows, identifiers, emails, section labels, or source assignment names
- use private source data only for aggregate and distributional calibration

Observed nonzero pools:

| Grade | Nonzero n | Mean | Median | SD | Q1 | Q3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 52 | 46.15 | 46.77 | 18.24 | 32.26 | 58.06 |
| 10 | 62 | 47.61 | 45.16 | 18.46 | 32.26 | 58.06 |
| 11 | 50 | 52.26 | 51.61 | 23.63 | 32.26 | 70.97 |
| 12 | 47 | 56.83 | 51.61 | 24.31 | 38.71 | 80.65 |

Earlier aggregate OLS benchmark:

| Quantity | Value |
| --- | ---: |
| Formula | `score ~ grade_level` |
| Nonzero n | 211 |
| Intercept | 12.085 |
| Grade slope | +3.672 points per grade |
| R-squared | 0.0351 |
| Slope SE | 1.3307 |
| Slope t-statistic | 2.7593 |

Interpretation for implementation:

```text
grade level has a positive but weak relationship with score
grade level should shift readiness prior modestly
historic present-score evidence should dominate once available
```

## Implementation Defaults

Use these defaults unless later documentation overrides them.

```yaml
random_seed: 20260604
replicate_count: 1000
score_bounds: [0, 100]
regression_formula: "score ~ grade_level"
calibration_sample_size_policy: "match_source_nonzero_count_by_grade"
grade_9_validation_n: 52
grade_10_validation_n: 62
grade_11_validation_n: 50
grade_12_validation_n: 47
present_score_zero_policy: "exclude_from_score_distribution"
absence_zero_policy: "model_separately"
calibration_distribution: "grade_specific_smoothed_empirical_quantile_bootstrap_with_local_jitter"
grade_prior_policy: "weak_shrunk_slope"
```

Use the existing Assignment 1 present-score bootstrap family:

```text
Q_grade(p) = interpolated empirical quantile function from nonzero scores for grade
bootstrap_p ~ Uniform(0, 1)
base_score = Q_grade(bootstrap_p)
local_spread = Q_grade(min(bootstrap_p + 0.05, 1)) - Q_grade(max(bootstrap_p - 0.05, 0))
jitter_sd = clamp(local_spread * 0.12, 0.75, 3.0)
sampled_score = clamp(base_score + Normal(0, jitter_sd), min_nonzero_source_score, 100)
```

## Grade-Level Calibration Workflow

Implement this as one connected workflow.

1. Load the private gradebook supplied at runtime.
2. Infer grade level from email suffix.
3. Extract column 9 scores.
4. Drop blank values and zeros.
5. Split nonzero scores into grade-specific pools.
6. Build one smoothed bootstrapped calibration distribution per grade.
7. Draw repeated same-size validation samples from the grade-specific calibration distributions.
8. For every repeated sample, compute validation metrics.
9. If validation passes, run `score ~ grade_level` on each repeated sample.
10. Summarize regression-output distributions.
11. Use the validated slope distribution to set a weak grade-level prior shift.

Important sample-size rule:

```text
The calibration distribution may be smooth or large.
The validation and regression samples should match source nonzero counts by grade.
```

This prevents the calibration population from creating fake certainty.

## Validation Targets

Validation checks whether repeated samples from the calibration distributions preserve the real grade-specific source structure.

Required grade-level summary metrics:

```text
mean
median
standard deviation
IQR
q05
q10
q25
q50
q75
q90
q95
min nonzero
max
```

Required distribution-distance metrics:

```text
KS statistic
Wasserstein distance
normalized Wasserstein distance
```

Use:

```text
normalized_wasserstein = wasserstein_distance / source_IQR
```

Required grade-gap metrics:

```text
grade 10 mean - grade 9 mean
grade 11 mean - grade 10 mean
grade 12 mean - grade 11 mean
grade 12 mean - grade 9 mean
grade 10 median - grade 9 median
grade 11 median - grade 10 median
grade 12 median - grade 11 median
grade 12 median - grade 9 median
```

Required regression metrics:

```text
slope
intercept
R-squared
P(slope > 0)
80% slope interval
95% slope interval
```

Required absence/zero checks:

```text
present-student zero rate = 0
absent-student observed score = 0
absence does not update observed posterior readiness
latent readiness still advances while absent
```

## Acceptance Rules

Do not use regression outputs for model calibration until the repeated-sampling validation passes.

Pass conditions:

- repeated-sample statistics are centered near source statistics
- source quantiles are reproduced without systematic drift
- KS and normalized Wasserstein distances are small and stable across grades
- grade-level mean and median gaps are not inflated or reversed by the generator
- regression slope direction aligns with the original OLS benchmark
- repeated-sample R-squared does not become artificially large

Review/recalibrate conditions:

- tails are too compressed or too exaggerated
- one grade drifts systematically away from its source pool
- grade gaps are inflated beyond the source evidence
- regression slope becomes much stronger than the original evidence supports
- R-squared rises in a way that suggests the generator over-encoded grade level

Do not frame validation as proof that the original sample represents a broader real population. Validation only checks source-faithfulness of the calibrated generator.

## Grade Prior Policy

Use the repeated regression-output distribution to set a weak grade-level prior shift.

Conceptual rule:

```text
grade_prior_shift = shrink(repeated_sample_slope_median)
```

Shrinkage guidance:

- if slope uncertainty is wide, shrink more
- if R-squared remains low, shrink more
- if `P(slope > 0)` is high but effect size is small, keep the effect positive but modest
- do not let grade level dominate historic present-score evidence

Recommended first implementation:

```text
grade_prior_shift_per_grade = 0.5 * repeated_sample_slope_median
```

If validation shows slope instability or inflated generator behavior, reduce the multiplier below `0.5` or do not apply a grade prior shift yet.

Model role:

```text
readiness_prior_i ~ Normal(mu_course_track + grade_prior_shift, sigma_prior)
```

Avoid:

```text
next_score = large_grade_weight * grade_level + other terms
```

## Reusable Longitudinal Score Engine

Use empirical Bayes for the first longitudinal model. Do not implement full MCMC for the first pass.

Conceptual function contract:

```text
generate_next_assessment_score(student_state, assessment_context)
```

Required inputs:

```text
prior assessment history
current latent readiness state
current observed posterior readiness state
grade level
course/track
teacher/section context
assessment window
transition type
attendance state
```

Required outputs:

```text
observed score
potential score
present/absent flag
generation mode
updated latent state
updated observed evidence state when present
updated attendance state
```

Core state:

```text
readiness_prior_i
latent_readiness_i
posterior_readiness_i
measurement_error
assessment_window
transition_type
course_track_effect
instructor_effect
section_effect
attendance_state
```

Supported transition types:

```text
initialize_readiness
school_year_growth
summer_atrophy
absent_no_update
```

General transition:

```text
latent_readiness_i =
    evolve(previous_latent_readiness_i, transition_type, context)

if present:
    observed_score_i = clamp(latent_readiness_i + observation_noise, 1, 100)
    posterior_readiness_i = update(observed_prior_i, observed_score_i, measurement_error)
else:
    observed_score_i = 0
    posterior_readiness_i unchanged
```

Naming rule:

```text
use latent_readiness
do not use latent_ability
```

Instructor effect wording:

```text
use instructor_effect or synthetic classroom growth effect
avoid teacher quality
```

## Future-Assignment Generation Rules

Assignments 02-14 should be populated sequentially by the reusable score engine.

Transition pattern:

| Transition | Type | Meaning |
| --- | --- | --- |
| BOY -> EOY | `school_year_growth` | growth during the academic year |
| EOY -> next BOY | `summer_atrophy` | retention loss or summer regression |
| no prior present score -> present score | `initialize_readiness` | first academic evidence |
| absent assessment | `absent_no_update` | observed zero, no observed-evidence update |

Summer atrophy belongs inside the same longitudinal engine as a distinct transition component. It is implemented for each end-of-year to next beginning-of-year transition after Assignment 02.

## Implemented Sequential Cases

Assignment 02 was the first school-year growth application. The current generator applies the same sequential contract across Assignments 02-14.

Odd-numbered assignments after Assignment 01 use `summer_atrophy`. Even-numbered assignments use `school_year_growth`.

### Case 1: Prior Present Evidence Exists And Current Student Is Present

```text
prior observed score
-> initialize posterior readiness
-> apply school-year growth or summer atrophy to latent readiness
-> draw current observed score from latent readiness plus observation noise
-> update posterior readiness from current present score
```

Potential score:

```text
latent_readiness_after =
    previous_latent_readiness
  + transition_component
  + regression_to_mean_component
  + instructor_effect
  + section_effect
  + course_track_effect
  + process_noise

observed_score_if_present =
    latent_readiness_after
  + observation_noise
```

### Case 2: No Prior Present Evidence And Current Student Is Present

```text
prior absences -> observed academic profile stays pending
hidden latent readiness still advances
current present score -> observe latent readiness with measurement noise
current score becomes first observed academic evidence
```

Prior observed zeros do not initialize or update observed posterior readiness.

### Case 3: Current Student Is Absent

```text
observed current score = 0
potential score remains blank
observed posterior readiness is not updated by current assignment
hidden latent readiness still advances
attendance/admin profile is updated
```

Allowed generation modes:

```text
first_present_evidence_from_latent
school_year_growth_from_latent_readiness
summer_atrophy_from_latent_readiness
absent_no_update
```

## Diagnostics To Produce

Private/internal outputs may include private source paths and calibration metadata.

Suggested private outputs:

```text
private derived data directory / grade-level-calibration-profile.json
private derived data directory / grade-level-validation-summary.csv
private derived data directory / grade-level-regression-replicates.csv
```

Public-safe outputs must not include private paths, real identifiers, emails, source rows, or exact source assignment names.

Suggested public-safe outputs:

```text
assignment_01_distribution_validation.md
assignment_01_quantile_calibration.svg
assignment_01_ecdf_overlay_by_grade.svg
assignment_01_bootstrap_slope_distribution.svg
assignment_01_distribution_distance_summary.csv
assignment_01_grade_gap_validation.csv
```

Recommended plots:

```text
quantile calibration plot by grade
ECDF overlay by grade
bootstrap slope distribution
KS / normalized Wasserstein bar chart by grade
grade-gap validation chart
```

## Research Notes

Use these as implementation constraints, not long report content.

- Observed standardized-test scores include measurement error.
- Historic present-score evidence should update observed posterior readiness rather than act as a raw score feature only.
- Instructor effects should be modeled as small random effects with shrinkage.
- Do not make causal claims about teacher quality.
- Absence/missingness must be modeled separately from academic readiness.
- Summer atrophy is part of the reusable score engine and is implemented as the EOY-to-next-BOY transition.

Reference anchors:

- Lockwood and Castellano on latent growth and measurement error: https://journals.sagepub.com/doi/abs/10.1177/0013164416659686
- McCaffrey, Lockwood, Koretz, and Hamilton on value-added model cautions: https://pmc.ncbi.nlm.nih.gov/articles/PMC2743034/
- AERA VAM statement: https://journals.sagepub.com/doi/abs/10.3102/0013189X15618385
- ASA VAM statement: https://www.amstat.org/policy/pdfs/ASA_VAM_Statement.pdf
- Missing-data research in value-added modeling: https://arxiv.org/abs/1108.2167

## Implementation Maintenance Checklist

The calibration layer should remain in place before changing future-assignment generation.

Required before changing calibration or transition rules:

- build grade-specific calibration distributions
- run repeated same-size validation samples
- generate validation summary tables
- generate regression-output distribution
- calculate weak grade prior shift
- write private calibration profile
- write public-safe diagnostic summaries and figures

Do not expand or materially change the longitudinal score engine if the grade-level calibration distribution fails validation.
