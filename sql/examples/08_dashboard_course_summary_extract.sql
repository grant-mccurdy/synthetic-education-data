SELECT
    school_year,
    course_id,
    course_name,
    course_track,
    COUNT(*) AS active_student_years,
    COUNT(DISTINCT section_id) AS active_sections,
    ROUND(AVG(CASE WHEN present_boy THEN boy_score ELSE NULL END), 2) AS boy_avg_present_score,
    ROUND(AVG(CASE WHEN present_eoy THEN eoy_score ELSE NULL END), 2) AS eoy_avg_present_score,
    ROUND(AVG(observed_growth_delta), 2) AS avg_observed_growth_delta,
    ROUND(AVG(CASE WHEN present_boy THEN 1.0 ELSE 0.0 END), 4) AS boy_present_rate,
    ROUND(AVG(CASE WHEN present_eoy THEN 1.0 ELSE 0.0 END), 4) AS eoy_present_rate
FROM mart.student_readiness
GROUP BY
    school_year,
    course_id,
    course_name,
    course_track
ORDER BY
    school_year,
    course_id;
