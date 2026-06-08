CREATE OR REPLACE TABLE mart.assignment_growth AS
SELECT
    school_year,
    school_year_offset,
    sis_user_id,
    student_label,
    grade_level,
    course_id,
    course_name,
    course_track,
    section_id,
    teacher_id,
    attendance_category,
    boy_assignment_label,
    eoy_assignment_label,
    boy_score,
    eoy_score,
    present_boy,
    present_eoy,
    observed_growth_delta,
    modeled_eoy_growth_delta,
    latent_readiness_after_boy,
    latent_readiness_after_eoy,
    latent_eoy_transition_delta,
    CASE
        WHEN NOT present_boy AND NOT present_eoy THEN 'absent_both_windows'
        WHEN NOT present_boy THEN 'first_evidence_eoy'
        WHEN NOT present_eoy THEN 'absent_eoy'
        WHEN observed_growth_delta >= 15 THEN 'large_positive_growth'
        WHEN observed_growth_delta >= 5 THEN 'positive_growth'
        WHEN observed_growth_delta BETWEEN -5 AND 5 THEN 'stable'
        WHEN observed_growth_delta < -5 THEN 'negative_growth'
        ELSE 'unclassified'
    END AS growth_band
FROM mart.student_readiness;
