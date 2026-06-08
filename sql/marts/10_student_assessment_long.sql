CREATE OR REPLACE TABLE mart.student_assessment_long AS
SELECT
    s.school_year,
    s.school_year_offset,
    s.sis_user_id,
    s.student_label,
    s.grade_level,
    s.course_id,
    c.course_name,
    c.track AS course_track,
    s.section_id,
    sec.section_label,
    s.teacher_id,
    sec.teacher_label,
    s.assignment_label,
    s.sequence_index,
    s.assessment_window,
    s.expected_transition_type,
    s.actual_transition_type,
    s.generation_mode,
    a.population_status,
    s.attendance_category,
    s.attendance_probability,
    s.observed_score AS score,
    CASE WHEN s.present THEN s.observed_score ELSE NULL END AS present_student_score,
    s.potential_score,
    s.posterior_readiness_after,
    s.growth_delta,
    s.latent_transition_type,
    s.latent_readiness_before,
    s.latent_readiness_after,
    s.latent_transition_delta,
    s.academic_profile_status,
    TRUE AS is_populated,
    s.present AS is_present,
    NOT s.present AND s.observed_score = 0 AS is_nonparticipation_zero
FROM raw.assessment_scores AS s
JOIN raw.courses AS c
    ON s.course_id = c.course_id
JOIN raw.sections AS sec
    ON s.school_year = sec.school_year
   AND s.section_id = sec.section_id
JOIN raw.assignments AS a
    ON s.assignment_label = a.assignment_label;
