SELECT
    da.school_year,
    da.assignment_label,
    dc.course_id,
    dc.course_name,
    dc.course_track,
    COUNT(*) AS student_rows,
    SUM(CASE WHEN fas.is_present THEN 1 ELSE 0 END) AS present_rows,
    ROUND(AVG(fas.present_student_score), 2) AS avg_present_score,
    ROUND(MIN(fas.present_student_score), 2) AS min_present_score,
    ROUND(QUANTILE_CONT(fas.present_student_score, 0.25), 2) AS q1_present_score,
    ROUND(MEDIAN(fas.present_student_score), 2) AS median_present_score,
    ROUND(QUANTILE_CONT(fas.present_student_score, 0.75), 2) AS q3_present_score,
    ROUND(MAX(fas.present_student_score), 2) AS max_present_score
FROM mart.fact_assessment_score AS fas
JOIN mart.dim_assignment AS da
    ON fas.assignment_dim_id = da.assignment_dim_id
JOIN mart.dim_course AS dc
    ON fas.course_dim_id = dc.course_dim_id
WHERE da.population_status = 'populated'
GROUP BY
    da.school_year,
    da.assignment_label,
    dc.course_id,
    dc.course_name,
    dc.course_track
ORDER BY
    da.school_year,
    da.assignment_label,
    dc.course_id;
