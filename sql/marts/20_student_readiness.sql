CREATE OR REPLACE TABLE mart.student_readiness AS
WITH yearly AS (
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
        section_label,
        teacher_id,
        teacher_label,
        attendance_category,
        attendance_probability,
        MAX(CASE WHEN assessment_window = 'beginning_of_year' THEN assignment_label END) AS boy_assignment_label,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN assignment_label END) AS eoy_assignment_label,
        MAX(CASE WHEN assessment_window = 'beginning_of_year' THEN score END) AS boy_score,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN score END) AS eoy_score,
        MAX(CASE WHEN assessment_window = 'beginning_of_year' THEN is_present END) AS present_boy,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN is_present END) AS present_eoy,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN growth_delta END) AS modeled_eoy_growth_delta,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN posterior_readiness_after END) AS posterior_readiness_after_eoy,
        MAX(CASE WHEN assessment_window = 'beginning_of_year' THEN latent_readiness_after END) AS latent_readiness_after_boy,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN latent_readiness_after END) AS latent_readiness_after_eoy,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN latent_transition_delta END) AS latent_eoy_transition_delta,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN generation_mode END) AS eoy_generation_mode,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN actual_transition_type END) AS eoy_transition_type,
        MAX(CASE WHEN assessment_window = 'end_of_year' THEN academic_profile_status END) AS eoy_academic_profile_status
    FROM mart.student_assessment_long
    GROUP BY
        school_year,
        school_year_offset,
        sis_user_id,
        student_label,
        grade_level,
        course_id,
        course_name,
        course_track,
        section_id,
        section_label,
        teacher_id,
        teacher_label,
        attendance_category,
        attendance_probability
)
SELECT
    *,
    CASE
        WHEN present_boy AND present_eoy THEN eoy_score - boy_score
        ELSE NULL
    END AS observed_growth_delta,
    eoy_academic_profile_status AS academic_profile_status
FROM yearly;
