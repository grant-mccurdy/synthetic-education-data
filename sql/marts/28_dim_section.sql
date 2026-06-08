CREATE OR REPLACE TABLE mart.dim_section AS
SELECT
    ROW_NUMBER() OVER (ORDER BY s.school_year, s.section_id) AS section_dim_id,
    s.school_year,
    s.school_year_offset,
    s.section_id,
    s.section_label,
    s.period_label,
    s.course_id,
    dc.course_dim_id,
    s.teacher_id,
    dt.teacher_dim_id,
    s.teacher_label,
    s.target_enrollment,
    s.max_capacity,
    s.class_size_band,
    s.section_growth_effect,
    s.teacher_growth_effect
FROM raw.sections AS s
JOIN mart.dim_course AS dc
    ON s.course_id = dc.course_id
JOIN mart.dim_teacher AS dt
    ON s.school_year = dt.school_year
   AND s.teacher_id = dt.teacher_id;
