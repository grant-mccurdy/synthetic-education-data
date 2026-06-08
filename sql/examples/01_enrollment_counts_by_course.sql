SELECT
    fle.school_year,
    dc.course_id,
    dc.course_name,
    dc.course_track,
    COUNT(*) AS active_enrollments
FROM mart.fact_lms_enrollment AS fle
JOIN mart.dim_course AS dc
    ON fle.course_dim_id = dc.course_dim_id
WHERE fle.is_active_enrollment
GROUP BY
    fle.school_year,
    dc.course_id,
    dc.course_name,
    dc.course_track
ORDER BY
    fle.school_year,
    active_enrollments DESC,
    dc.course_id;
