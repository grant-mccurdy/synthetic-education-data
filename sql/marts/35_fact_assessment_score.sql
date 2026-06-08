CREATE OR REPLACE TABLE mart.fact_assessment_score AS
SELECT
    ROW_NUMBER() OVER (
        ORDER BY sal.school_year, sal.sis_user_id, sal.sequence_index
    ) AS assessment_score_fact_id,
    ds.student_dim_id,
    dc.course_dim_id,
    dsec.section_dim_id,
    dt.teacher_dim_id,
    da.assignment_dim_id,
    sal.school_year,
    sal.school_year_offset,
    sal.sis_user_id,
    sal.course_id,
    sal.section_id,
    sal.teacher_id,
    sal.assignment_label,
    sal.sequence_index,
    sal.assessment_window,
    sal.expected_transition_type,
    sal.actual_transition_type,
    sal.generation_mode,
    sal.population_status,
    sal.score,
    sal.present_student_score,
    sal.potential_score,
    sal.posterior_readiness_after,
    sal.growth_delta,
    sal.latent_transition_type,
    sal.latent_readiness_before,
    sal.latent_readiness_after,
    sal.latent_transition_delta,
    sal.is_populated,
    sal.is_present,
    sal.is_nonparticipation_zero
FROM mart.student_assessment_long AS sal
JOIN mart.dim_student AS ds
    ON sal.sis_user_id = ds.sis_user_id
JOIN mart.dim_course AS dc
    ON sal.course_id = dc.course_id
JOIN mart.dim_section AS dsec
    ON sal.school_year = dsec.school_year
   AND sal.section_id = dsec.section_id
JOIN mart.dim_teacher AS dt
    ON sal.school_year = dt.school_year
   AND sal.teacher_id = dt.teacher_id
JOIN mart.dim_assignment AS da
    ON sal.assignment_label = da.assignment_label;
