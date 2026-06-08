CREATE OR REPLACE TABLE mart.canvas_course_pipeline_audit AS
WITH canonical_counts AS (
    SELECT
        e.school_year,
        e.course_id,
        COUNT(*) AS canonical_enrollment_count,
        COUNT(DISTINCT e.section_id) AS canonical_section_count,
        COUNT(DISTINCT e.teacher_id) AS canonical_teacher_count
    FROM raw.enrollments AS e
    GROUP BY e.school_year, e.course_id
),
canvas_counts AS (
    SELECT
        c.school_year,
        c.course_id,
        c.canvas_course_id,
        c.course_name,
        c.source_system,
        c.profile_path,
        COUNT(*) AS canvas_enrollment_count,
        COUNT(DISTINCT e.section_id) AS canvas_section_count,
        COUNT(DISTINCT s.teacher_id) AS canvas_teacher_count
    FROM raw_canvas.courses AS c
    LEFT JOIN raw_canvas.enrollments AS e
        ON c.canvas_course_id = e.canvas_course_id
    LEFT JOIN raw_canvas.sections AS s
        ON c.canvas_course_id = s.canvas_course_id
       AND e.section_id = s.section_id
    GROUP BY
        c.school_year,
        c.course_id,
        c.canvas_course_id,
        c.course_name,
        c.source_system,
        c.profile_path
)
SELECT
    COALESCE(cc.school_year, cn.school_year) AS school_year,
    COALESCE(cc.course_id, cn.course_id) AS course_id,
    cc.canvas_course_id,
    cc.course_name,
    cc.source_system,
    cc.profile_path,
    cn.canonical_enrollment_count,
    cc.canvas_enrollment_count,
    cn.canonical_section_count,
    cc.canvas_section_count,
    cn.canonical_teacher_count,
    cc.canvas_teacher_count,
    CASE
        WHEN cn.course_id IS NULL THEN 'missing_from_canonical'
        WHEN cc.course_id IS NULL THEN 'missing_from_canvas_extract'
        WHEN cn.canonical_enrollment_count != cc.canvas_enrollment_count THEN 'enrollment_count_mismatch'
        WHEN cn.canonical_section_count != cc.canvas_section_count THEN 'section_count_mismatch'
        WHEN cn.canonical_teacher_count != cc.canvas_teacher_count THEN 'teacher_count_mismatch'
        ELSE 'matched'
    END AS audit_status
FROM canvas_counts AS cc
FULL OUTER JOIN canonical_counts AS cn
    ON cc.school_year = cn.school_year
   AND cc.course_id = cn.course_id;
