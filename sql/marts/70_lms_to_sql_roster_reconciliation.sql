CREATE OR REPLACE TABLE mart.lms_to_sql_roster_reconciliation AS
SELECT
    COALESCE(e.school_year, c.school_year) AS school_year,
    COALESCE(e.sis_user_id, c.sis_user_id) AS sis_user_id,
    e.student_label AS canonical_student_label,
    c.student_label AS canvas_student_label,
    e.course_id AS canonical_course_id,
    c.course_id AS canvas_course_id,
    e.section_id AS canonical_section_id,
    c.section_id AS canvas_section_id,
    e.teacher_id AS canonical_teacher_id,
    c.teacher_id AS canvas_teacher_id,
    e.enrollment_status AS canonical_enrollment_status,
    c.enrollment_status AS canvas_enrollment_status,
    c.email AS canvas_email,
    CASE
        WHEN e.sis_user_id IS NULL THEN 'missing_from_canonical_enrollments'
        WHEN c.sis_user_id IS NULL THEN 'missing_from_canvas_extract'
        WHEN e.course_id != c.course_id THEN 'course_mismatch'
        WHEN e.section_id != c.section_id THEN 'section_mismatch'
        WHEN e.teacher_id != c.teacher_id THEN 'teacher_mismatch'
        WHEN e.enrollment_status != c.enrollment_status THEN 'status_mismatch'
        ELSE 'matched'
    END AS reconciliation_status
FROM raw.enrollments AS e
FULL OUTER JOIN mart.canvas_roster_sql_extract AS c
    ON e.school_year = c.school_year
   AND e.sis_user_id = c.sis_user_id;
