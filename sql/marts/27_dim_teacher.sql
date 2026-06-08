CREATE OR REPLACE TABLE mart.dim_teacher AS
SELECT
    ROW_NUMBER() OVER (ORDER BY t.school_year, t.teacher_id) AS teacher_dim_id,
    t.school_year,
    t.teacher_id,
    t.teacher_label,
    t.target_section_load,
    t.teacher_growth_effect
FROM raw.teachers AS t;
