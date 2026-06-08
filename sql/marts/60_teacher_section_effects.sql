CREATE OR REPLACE TABLE mart.teacher_section_effects AS
SELECT
    sr.school_year,
    sr.school_year_offset,
    sr.teacher_id,
    sr.teacher_label,
    sr.section_id,
    sr.section_label,
    sr.course_id,
    sr.course_name,
    sr.course_track,
    sec.class_size_band,
    sec.target_enrollment,
    sec.max_capacity,
    sec.section_growth_effect,
    sec.teacher_growth_effect,
    COUNT(*) AS enrolled_students,
    ROUND(AVG(sr.boy_score), 2) AS boy_avg_all_students,
    ROUND(AVG(sr.eoy_score), 2) AS eoy_avg_all_students,
    ROUND(AVG(sr.observed_growth_delta), 2) AS avg_observed_growth_delta,
    ROUND(AVG(CASE WHEN sr.present_eoy THEN 1.0 ELSE 0.0 END), 4) AS eoy_present_rate
FROM mart.student_readiness AS sr
JOIN raw.sections AS sec
    ON sr.school_year = sec.school_year
   AND sr.section_id = sec.section_id
GROUP BY
    sr.school_year,
    sr.school_year_offset,
    sr.teacher_id,
    sr.teacher_label,
    sr.section_id,
    sr.section_label,
    sr.course_id,
    sr.course_name,
    sr.course_track,
    sec.class_size_band,
    sec.target_enrollment,
    sec.max_capacity,
    sec.section_growth_effect,
    sec.teacher_growth_effect;
