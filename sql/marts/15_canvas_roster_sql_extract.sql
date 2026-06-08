CREATE OR REPLACE TABLE mart.canvas_roster_sql_extract AS
SELECT
    ce.extraction_batch_id,
    cc.source_system,
    cc.school_year,
    ce.canvas_course_id,
    ce.course_id,
    cc.course_name,
    cc.track AS course_track,
    ce.section_id,
    cs.section_label,
    cs.period_label,
    cs.teacher_id,
    cs.teacher_label,
    ce.sis_user_id,
    ce.student_label,
    ce.email,
    ce.grade_level,
    ce.enrollment_status
FROM raw_canvas.enrollments AS ce
JOIN raw_canvas.courses AS cc
    ON ce.canvas_course_id = cc.canvas_course_id
JOIN raw_canvas.sections AS cs
    ON ce.canvas_course_id = cs.canvas_course_id
   AND ce.school_year = cs.school_year
   AND ce.section_id = cs.section_id;
