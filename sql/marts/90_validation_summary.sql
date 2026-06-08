CREATE OR REPLACE TABLE mart.validation_summary AS
WITH expected AS (
    SELECT
        COUNT(*) AS school_year_count,
        SUM(active_student_count) AS active_student_years,
        SUM(active_student_count) * 2 AS assessment_score_rows,
        SUM(section_count) AS section_count
    FROM raw.school_years
),
checks AS (
    SELECT
        'school_year_count' AS check_name,
        CAST((SELECT COUNT(*) FROM raw.school_years) AS VARCHAR) AS observed_value,
        '7' AS expected_value,
        (SELECT COUNT(*) FROM raw.school_years) = 7 AS passed
    UNION ALL
    SELECT
        'active_student_years',
        CAST((SELECT COUNT(*) FROM raw.enrollments) AS VARCHAR),
        CAST((SELECT active_student_years FROM expected) AS VARCHAR),
        (SELECT COUNT(*) FROM raw.enrollments) = (SELECT active_student_years FROM expected)
    UNION ALL
    SELECT
        'all_ever_student_count',
        CAST((SELECT COUNT(*) FROM raw.students) AS VARCHAR),
        CAST((SELECT COUNT(DISTINCT sis_user_id) FROM raw.enrollments) AS VARCHAR),
        (SELECT COUNT(*) FROM raw.students) = (SELECT COUNT(DISTINCT sis_user_id) FROM raw.enrollments)
    UNION ALL
    SELECT
        'course_count',
        CAST((SELECT COUNT(*) FROM raw.courses) AS VARCHAR),
        '9',
        (SELECT COUNT(*) FROM raw.courses) = 9
    UNION ALL
    SELECT
        'section_count',
        CAST((SELECT COUNT(*) FROM raw.sections) AS VARCHAR),
        CAST((SELECT section_count FROM expected) AS VARCHAR),
        (SELECT COUNT(*) FROM raw.sections) = (SELECT section_count FROM expected)
    UNION ALL
    SELECT
        'teacher_year_count',
        CAST((SELECT COUNT(*) FROM raw.teachers) AS VARCHAR),
        CAST((SELECT school_year_count * 5 FROM expected) AS VARCHAR),
        (SELECT COUNT(*) FROM raw.teachers) = (SELECT school_year_count * 5 FROM expected)
    UNION ALL
    SELECT
        'assignment_count',
        CAST((SELECT COUNT(*) FROM raw.assignments) AS VARCHAR),
        '14',
        (SELECT COUNT(*) FROM raw.assignments) = 14
    UNION ALL
    SELECT
        'assessment_score_rows',
        CAST((SELECT COUNT(*) FROM raw.assessment_scores) AS VARCHAR),
        CAST((SELECT assessment_score_rows FROM expected) AS VARCHAR),
        (SELECT COUNT(*) FROM raw.assessment_scores) = (SELECT assessment_score_rows FROM expected)
    UNION ALL
    SELECT
        'one_enrollment_per_active_student_year',
        CAST((
            SELECT COUNT(*)
            FROM (
                SELECT school_year, sis_user_id
                FROM raw.enrollments
                GROUP BY school_year, sis_user_id
                HAVING COUNT(*) = 1
            )
        ) AS VARCHAR),
        CAST((SELECT active_student_years FROM expected) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM (
                SELECT school_year, sis_user_id
                FROM raw.enrollments
                GROUP BY school_year, sis_user_id
                HAVING COUNT(*) = 1
            )
        ) = (SELECT active_student_years FROM expected)
    UNION ALL
    SELECT
        'score_bounds_all_assignments',
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE observed_score BETWEEN 0 AND 100
              AND (potential_score IS NULL OR potential_score BETWEEN 1 AND 100)
        ) AS VARCHAR),
        CAST((SELECT assessment_score_rows FROM expected) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE observed_score BETWEEN 0 AND 100
              AND (potential_score IS NULL OR potential_score BETWEEN 1 AND 100)
        ) = (SELECT assessment_score_rows FROM expected)
    UNION ALL
    SELECT
        'present_scores_nonzero',
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE present AND observed_score > 0
        ) AS VARCHAR),
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE present
        ) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE present AND observed_score > 0
        ) = (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE present
        )
    UNION ALL
    SELECT
        'absent_scores_zero',
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present AND observed_score = 0
        ) AS VARCHAR),
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present
        ) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present AND observed_score = 0
        ) = (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present
        )
    UNION ALL
    SELECT
        'latent_readiness_all_assessments',
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE latent_readiness_after BETWEEN 1 AND 100
        ) AS VARCHAR),
        CAST((SELECT assessment_score_rows FROM expected) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE latent_readiness_after BETWEEN 1 AND 100
        ) = (SELECT assessment_score_rows FROM expected)
    UNION ALL
    SELECT
        'absent_observed_readiness_unchanged',
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present
              AND posterior_readiness_after IS NULL
              AND potential_score IS NULL
        ) AS VARCHAR),
        CAST((
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present
        ) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present
              AND posterior_readiness_after IS NULL
              AND potential_score IS NULL
        ) = (
            SELECT COUNT(*)
            FROM raw.assessment_scores
            WHERE NOT present
        )
    UNION ALL
    SELECT
        'canvas_sql_enrollment_rows',
        CAST((SELECT COUNT(*) FROM raw_canvas.enrollments) AS VARCHAR),
        CAST((SELECT active_student_years FROM expected) AS VARCHAR),
        (SELECT COUNT(*) FROM raw_canvas.enrollments) = (SELECT active_student_years FROM expected)
    UNION ALL
    SELECT
        'canvas_unique_enrollment_per_student_year',
        CAST((
            SELECT COUNT(*)
            FROM (
                SELECT school_year, sis_user_id
                FROM raw_canvas.enrollments
                GROUP BY school_year, sis_user_id
                HAVING COUNT(*) = 1
            )
        ) AS VARCHAR),
        CAST((SELECT active_student_years FROM expected) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM (
                SELECT school_year, sis_user_id
                FROM raw_canvas.enrollments
                GROUP BY school_year, sis_user_id
                HAVING COUNT(*) = 1
            )
        ) = (SELECT active_student_years FROM expected)
    UNION ALL
    SELECT
        'canvas_to_canonical_roster_reconciliation',
        CAST((
            SELECT COUNT(*)
            FROM mart.lms_to_sql_roster_reconciliation
            WHERE reconciliation_status = 'matched'
        ) AS VARCHAR),
        CAST((SELECT active_student_years FROM expected) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM mart.lms_to_sql_roster_reconciliation
            WHERE reconciliation_status = 'matched'
        ) = (SELECT active_student_years FROM expected)
    UNION ALL
    SELECT
        'canvas_course_pipeline_audit',
        CAST((
            SELECT COUNT(*)
            FROM mart.canvas_course_pipeline_audit
            WHERE audit_status = 'matched'
        ) AS VARCHAR),
        CAST((SELECT COUNT(*) FROM raw_canvas.courses) AS VARCHAR),
        (
            SELECT COUNT(*)
            FROM mart.canvas_course_pipeline_audit
            WHERE audit_status = 'matched'
        ) = (SELECT COUNT(*) FROM raw_canvas.courses)
    UNION ALL
    SELECT
        'fact_assessment_score_rows',
        CAST((SELECT COUNT(*) FROM mart.fact_assessment_score) AS VARCHAR),
        CAST((SELECT assessment_score_rows FROM expected) AS VARCHAR),
        (SELECT COUNT(*) FROM mart.fact_assessment_score) = (SELECT assessment_score_rows FROM expected)
    UNION ALL
    SELECT
        'fact_lms_enrollment_rows',
        CAST((SELECT COUNT(*) FROM mart.fact_lms_enrollment) AS VARCHAR),
        CAST((SELECT active_student_years FROM expected) AS VARCHAR),
        (SELECT COUNT(*) FROM mart.fact_lms_enrollment) = (SELECT active_student_years FROM expected)
)
SELECT
    check_name,
    observed_value,
    expected_value,
    CASE WHEN passed THEN 'pass' ELSE 'fail' END AS status
FROM checks;
