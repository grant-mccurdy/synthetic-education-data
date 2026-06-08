SELECT
    school_year,
    course_id,
    course_name,
    section_id,
    section_label,
    teacher_id,
    teacher_label,
    COUNT(*) AS matched_student_years,
    ROUND(AVG(observed_growth_delta), 2) AS avg_growth_delta
FROM mart.student_readiness
WHERE present_boy
  AND present_eoy
GROUP BY
    school_year,
    course_id,
    course_name,
    section_id,
    section_label,
    teacher_id,
    teacher_label
ORDER BY
    school_year,
    avg_growth_delta DESC,
    section_id;
