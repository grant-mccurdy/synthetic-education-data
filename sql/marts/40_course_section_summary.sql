CREATE OR REPLACE TABLE mart.course_section_summary AS
SELECT
    school_year,
    school_year_offset,
    course_id,
    course_name,
    course_track,
    section_id,
    section_label,
    teacher_id,
    teacher_label,
    COUNT(*) AS enrolled_students,
    SUM(CASE WHEN present_boy THEN 1 ELSE 0 END) AS boy_present_count,
    SUM(CASE WHEN present_eoy THEN 1 ELSE 0 END) AS eoy_present_count,
    ROUND(AVG(CASE WHEN present_boy THEN boy_score ELSE NULL END), 2) AS boy_avg_present_score,
    ROUND(AVG(CASE WHEN present_eoy THEN eoy_score ELSE NULL END), 2) AS eoy_avg_present_score,
    ROUND(AVG(observed_growth_delta), 2) AS avg_observed_growth_delta,
    ROUND(1 - AVG(CASE WHEN present_boy THEN 1.0 ELSE 0.0 END), 4) AS boy_nonparticipation_rate,
    ROUND(1 - AVG(CASE WHEN present_eoy THEN 1.0 ELSE 0.0 END), 4) AS eoy_nonparticipation_rate
FROM mart.student_readiness
GROUP BY
    school_year,
    school_year_offset,
    course_id,
    course_name,
    course_track,
    section_id,
    section_label,
    teacher_id,
    teacher_label;
