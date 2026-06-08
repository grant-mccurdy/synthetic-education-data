SELECT
    da.school_year,
    da.assignment_label,
    ds.attendance_category,
    COUNT(*) AS student_assignment_rows,
    SUM(CASE WHEN fas.is_present THEN 1 ELSE 0 END) AS present_rows,
    SUM(CASE WHEN fas.is_nonparticipation_zero THEN 1 ELSE 0 END) AS nonparticipation_zero_rows,
    ROUND(1 - AVG(CASE WHEN fas.is_present THEN 1.0 ELSE 0.0 END), 4) AS nonparticipation_rate
FROM mart.fact_assessment_score AS fas
JOIN mart.dim_student AS ds
    ON fas.student_dim_id = ds.student_dim_id
JOIN mart.dim_assignment AS da
    ON fas.assignment_dim_id = da.assignment_dim_id
WHERE da.population_status = 'populated'
GROUP BY
    da.school_year,
    da.assignment_label,
    ds.attendance_category
ORDER BY
    da.school_year,
    da.assignment_label,
    nonparticipation_rate DESC;
