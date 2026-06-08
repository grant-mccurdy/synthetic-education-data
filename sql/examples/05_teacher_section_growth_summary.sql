SELECT
    school_year,
    teacher_id,
    teacher_label,
    section_id,
    section_label,
    course_id,
    course_name,
    enrolled_students,
    eoy_present_rate,
    avg_observed_growth_delta,
    section_growth_effect,
    teacher_growth_effect
FROM mart.teacher_section_effects
ORDER BY
    school_year,
    avg_observed_growth_delta DESC NULLS LAST,
    teacher_id,
    section_id;
