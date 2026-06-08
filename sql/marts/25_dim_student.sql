CREATE OR REPLACE TABLE mart.dim_student AS
SELECT
    ROW_NUMBER() OVER (ORDER BY s.sis_user_id) AS student_dim_id,
    s.sis_user_id,
    s.student_label,
    s.export_id,
    s.canvas_gradebook_section,
    s.graduation_year,
    s.graduation_year_suffix,
    s.cohort_label,
    s.entry_school_year,
    s.entry_school_year_offset,
    s.graduation_school_year,
    s.graduation_school_year_offset,
    s.attendance_category,
    s.attendance_probability,
    s.latest_academic_profile_status,
    s.latest_posterior_readiness,
    s.latest_latent_readiness,
    s.latest_present_score
FROM raw.students AS s;
