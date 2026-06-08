CREATE OR REPLACE TABLE mart.fact_lms_enrollment AS
SELECT
    ROW_NUMBER() OVER (
        ORDER BY cre.extraction_batch_id, cre.school_year, cre.canvas_course_id, cre.section_id, cre.sis_user_id
    ) AS lms_enrollment_fact_id,
    ds.student_dim_id,
    dc.course_dim_id,
    dsec.section_dim_id,
    dt.teacher_dim_id,
    cre.extraction_batch_id,
    cre.source_system,
    cre.school_year,
    cre.canvas_course_id,
    cre.course_id,
    cre.section_id,
    cre.teacher_id,
    cre.sis_user_id,
    cre.grade_level,
    cre.enrollment_status,
    cre.enrollment_status = 'active' AS is_active_enrollment,
    rec.reconciliation_status
FROM mart.canvas_roster_sql_extract AS cre
JOIN mart.dim_student AS ds
    ON cre.sis_user_id = ds.sis_user_id
JOIN mart.dim_course AS dc
    ON cre.course_id = dc.course_id
JOIN mart.dim_section AS dsec
    ON cre.school_year = dsec.school_year
   AND cre.section_id = dsec.section_id
JOIN mart.dim_teacher AS dt
    ON cre.school_year = dt.school_year
   AND cre.teacher_id = dt.teacher_id
LEFT JOIN mart.lms_to_sql_roster_reconciliation AS rec
    ON cre.school_year = rec.school_year
   AND cre.sis_user_id = rec.sis_user_id;
