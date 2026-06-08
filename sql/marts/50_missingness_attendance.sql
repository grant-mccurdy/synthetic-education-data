CREATE OR REPLACE TABLE mart.missingness_attendance AS
SELECT
    school_year,
    school_year_offset,
    grade_level,
    course_track,
    attendance_category,
    COUNT(*) AS student_year_count,
    ROUND(AVG(attendance_probability), 4) AS avg_attendance_probability,
    ROUND(1 - AVG(CASE WHEN present_boy THEN 1.0 ELSE 0.0 END), 4) AS boy_nonparticipation_rate,
    ROUND(1 - AVG(CASE WHEN present_eoy THEN 1.0 ELSE 0.0 END), 4) AS eoy_nonparticipation_rate,
    ROUND(AVG(CASE WHEN present_boy THEN boy_score ELSE NULL END), 2) AS boy_avg_present_score,
    ROUND(AVG(CASE WHEN present_eoy THEN eoy_score ELSE NULL END), 2) AS eoy_avg_present_score,
    ROUND(AVG(observed_growth_delta), 2) AS avg_observed_growth_delta
FROM mart.student_readiness
GROUP BY
    school_year,
    school_year_offset,
    grade_level,
    course_track,
    attendance_category;
