SELECT
    school_year,
    sis_user_id,
    canonical_student_label,
    canvas_student_label,
    canonical_course_id,
    canvas_course_id,
    canonical_section_id,
    canvas_section_id,
    reconciliation_status
FROM mart.lms_to_sql_roster_reconciliation
WHERE reconciliation_status != 'matched'
ORDER BY
    school_year,
    reconciliation_status,
    sis_user_id;
