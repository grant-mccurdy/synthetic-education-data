# Public Safety Boundary

This repository is intended to be public-safe. It may contain synthetic data, synthetic identifiers, generalized methodology, validation scripts, and generated public-safe artifacts.

## Allowed

The public repository may include:

- fake student names and IDs
- fake LMS-style emails on the reserved `schoolname.example` domain
- fake teacher labels
- fake section labels
- standard course names
- synthetic enrollments
- synthetic assignment scores
- generalized calibration parameters
- public-safe aggregate calibration diagnostics
- generated synthetic CSV and JSON artifacts
- methodology documentation

## Not Allowed

Do not commit:

- real student names
- real student emails or IDs
- real rosters
- raw LMS exports
- private Canvas URLs or IDs
- real teacher names
- internal section labels
- exact source rows
- exact source assignment names
- private calibration/debug profiles
- private source paths
- API keys, tokens, or credentials

## Calibration Policy

Private reference data may inform local methodology development, but public code must not require private files to run.

Public generator code should use:

- synthetic defaults
- generalized parameters
- public-safe summary anchors
- validation checks
- optional aggregate calibration summaries

Public generator code should not use:

- hard-coded private file paths
- raw private distributions
- source row sampling
- private identity fields
- private debug outputs

Calibration scripts may read private local source files only when the caller supplies a path at runtime. Public calibration outputs must omit private paths, source rows, identifiers, emails, and private section labels.

## Release Check

Before committing or pushing:

```bash
make all
```

The validator checks artifact shape, row counts, enrollment consistency, score bounds, assignment population policy, longitudinal method behavior, and banned private/source strings.
