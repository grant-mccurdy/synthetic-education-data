WITH readiness AS (
    SELECT
        school_year,
        course_id,
        course_name,
        course_track,
        grade_level,
        posterior_readiness_after_eoy,
        CASE
            WHEN posterior_readiness_after_eoy >= 85 THEN 'advanced'
            WHEN posterior_readiness_after_eoy >= 70 THEN 'ready'
            WHEN posterior_readiness_after_eoy >= 55 THEN 'watch'
            WHEN posterior_readiness_after_eoy IS NULL THEN 'not_observed'
            ELSE 'intervention'
        END AS readiness_band
    FROM mart.student_readiness
)
SELECT
    school_year,
    course_id,
    course_name,
    course_track,
    grade_level,
    readiness_band,
    COUNT(*) AS student_year_count
FROM readiness
GROUP BY
    school_year,
    course_id,
    course_name,
    course_track,
    grade_level,
    readiness_band
ORDER BY
    school_year,
    course_id,
    grade_level,
    readiness_band;
