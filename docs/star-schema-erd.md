# DuckDB Star Schema ERD

The DuckDB warehouse includes a public-safe star schema for downstream assessment reporting.

```mermaid
erDiagram
    dim_student ||--o{ fact_assessment_score : "student_dim_id"
    dim_course ||--o{ fact_assessment_score : "course_dim_id"
    dim_section ||--o{ fact_assessment_score : "section_dim_id"
    dim_teacher ||--o{ fact_assessment_score : "teacher_dim_id"
    dim_assignment ||--o{ fact_assessment_score : "assignment_dim_id"

    dim_student ||--o{ fact_lms_enrollment : "student_dim_id"
    dim_course ||--o{ fact_lms_enrollment : "course_dim_id"
    dim_section ||--o{ fact_lms_enrollment : "section_dim_id"
    dim_teacher ||--o{ fact_lms_enrollment : "teacher_dim_id"

    dim_student {
        integer student_dim_id
        string sis_user_id
        string student_label
        integer graduation_year
        string cohort_label
        string attendance_category
    }

    dim_course {
        integer course_dim_id
        string course_id
        string course_name
        string course_track
    }

    dim_section {
        integer section_dim_id
        string school_year
        string section_id
        string section_label
        integer course_dim_id
        integer teacher_dim_id
    }

    dim_teacher {
        integer teacher_dim_id
        string school_year
        string teacher_id
        string teacher_label
        double teacher_growth_effect
    }

    dim_assignment {
        integer assignment_dim_id
        string assignment_label
        integer sequence_index
        string school_year
        string assessment_window
        string population_status
    }

    fact_assessment_score {
        integer assessment_score_fact_id
        integer student_dim_id
        integer course_dim_id
        integer section_dim_id
        integer teacher_dim_id
        integer assignment_dim_id
        string school_year
        double score
        double posterior_readiness_after
        double latent_readiness_after
        double latent_transition_delta
        boolean is_present
    }

    fact_lms_enrollment {
        integer lms_enrollment_fact_id
        integer student_dim_id
        integer course_dim_id
        integer section_dim_id
        integer teacher_dim_id
        string school_year
        string source_system
        string reconciliation_status
    }
```

## Grain

- `fact_assessment_score`: one row per active synthetic student assessment window.
- `fact_lms_enrollment`: one row per active synthetic student-year Canvas-derived enrollment.

## Use Cases

- assessment score distributions by course, section, teacher, and assignment
- assignment growth diagnostics
- non-participation and attendance checks
- LMS roster reconciliation before dashboarding
- dashboard-ready extracts for `assessment-intelligence`
