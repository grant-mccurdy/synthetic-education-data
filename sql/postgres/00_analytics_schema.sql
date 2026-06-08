DROP VIEW IF EXISTS public.student_readiness_extract;
DROP VIEW IF EXISTS public.lms_enrollment_reconciliation;
DROP VIEW IF EXISTS public.nonparticipation_by_group;
DROP VIEW IF EXISTS public.assignment_growth_by_course;
DROP VIEW IF EXISTS public.course_section_performance;

DROP SCHEMA IF EXISTS analytics CASCADE;
DROP SCHEMA IF EXISTS lms CASCADE;

CREATE SCHEMA lms;
CREATE SCHEMA analytics;

CREATE TABLE lms.canvas_courses (
    extraction_batch_id text NOT NULL,
    source_system text NOT NULL,
    school_year text NOT NULL,
    canvas_course_id text PRIMARY KEY,
    course_id text NOT NULL,
    course_name text NOT NULL,
    course_track text NOT NULL
);

CREATE TABLE lms.canvas_sections (
    extraction_batch_id text NOT NULL,
    canvas_course_id text NOT NULL REFERENCES lms.canvas_courses(canvas_course_id),
    course_id text NOT NULL,
    section_id text NOT NULL,
    school_year text NOT NULL,
    section_label text NOT NULL,
    period_label text NOT NULL,
    teacher_id text NOT NULL,
    teacher_label text NOT NULL,
    PRIMARY KEY (canvas_course_id, school_year, section_id)
);

CREATE TABLE lms.canvas_enrollments (
    extraction_batch_id text NOT NULL,
    canvas_course_id text NOT NULL REFERENCES lms.canvas_courses(canvas_course_id),
    school_year text NOT NULL,
    course_id text NOT NULL,
    section_id text NOT NULL,
    sis_user_id text NOT NULL,
    student_label text NOT NULL,
    email text NOT NULL,
    grade_level integer NOT NULL,
    enrollment_status text NOT NULL,
    PRIMARY KEY (school_year, sis_user_id)
);

CREATE TABLE analytics.dim_student (
    student_dim_id integer PRIMARY KEY,
    sis_user_id text NOT NULL UNIQUE,
    student_label text NOT NULL,
    export_id text NOT NULL,
    canvas_gradebook_section text NOT NULL,
    graduation_year integer NOT NULL,
    graduation_year_suffix text NOT NULL,
    cohort_label text NOT NULL,
    entry_school_year text NOT NULL,
    entry_school_year_offset integer NOT NULL,
    graduation_school_year text,
    graduation_school_year_offset integer NOT NULL,
    attendance_category text NOT NULL,
    attendance_probability double precision NOT NULL,
    latest_academic_profile_status text NOT NULL,
    latest_posterior_readiness double precision,
    latest_latent_readiness double precision,
    latest_present_score double precision
);

CREATE TABLE analytics.dim_course (
    course_dim_id integer PRIMARY KEY,
    course_id text NOT NULL UNIQUE,
    course_name text NOT NULL,
    course_track text NOT NULL,
    sequence_order integer NOT NULL,
    current_year_eligible boolean NOT NULL
);

CREATE TABLE analytics.dim_teacher (
    teacher_dim_id integer PRIMARY KEY,
    school_year text NOT NULL,
    teacher_id text NOT NULL,
    teacher_label text NOT NULL,
    target_section_load integer NOT NULL,
    teacher_growth_effect double precision NOT NULL,
    UNIQUE (school_year, teacher_id)
);

CREATE TABLE analytics.dim_section (
    section_dim_id integer PRIMARY KEY,
    school_year text NOT NULL,
    school_year_offset integer NOT NULL,
    section_id text NOT NULL,
    section_label text NOT NULL,
    period_label text NOT NULL,
    course_id text NOT NULL,
    course_dim_id integer NOT NULL REFERENCES analytics.dim_course(course_dim_id),
    teacher_id text NOT NULL,
    teacher_dim_id integer NOT NULL REFERENCES analytics.dim_teacher(teacher_dim_id),
    teacher_label text NOT NULL,
    target_enrollment integer NOT NULL,
    max_capacity integer NOT NULL,
    class_size_band text NOT NULL,
    section_growth_effect double precision NOT NULL,
    teacher_growth_effect double precision NOT NULL,
    UNIQUE (school_year, section_id)
);

CREATE TABLE analytics.dim_assignment (
    assignment_dim_id integer PRIMARY KEY,
    assignment_label text NOT NULL UNIQUE,
    sequence_index integer NOT NULL,
    school_year text NOT NULL,
    school_year_offset integer NOT NULL,
    assessment_window text NOT NULL,
    transition_type text NOT NULL,
    population_status text NOT NULL
);

CREATE TABLE analytics.student_readiness (
    school_year text NOT NULL,
    school_year_offset integer NOT NULL,
    sis_user_id text NOT NULL REFERENCES analytics.dim_student(sis_user_id),
    student_label text NOT NULL,
    grade_level integer NOT NULL,
    course_id text NOT NULL,
    course_name text NOT NULL,
    course_track text NOT NULL,
    section_id text NOT NULL,
    section_label text NOT NULL,
    teacher_id text NOT NULL,
    teacher_label text NOT NULL,
    attendance_category text NOT NULL,
    attendance_probability double precision NOT NULL,
    boy_assignment_label text NOT NULL,
    eoy_assignment_label text NOT NULL,
    boy_score double precision NOT NULL,
    eoy_score double precision NOT NULL,
    present_boy boolean NOT NULL,
    present_eoy boolean NOT NULL,
    modeled_eoy_growth_delta double precision,
    posterior_readiness_after_eoy double precision,
    latent_readiness_after_boy double precision,
    latent_readiness_after_eoy double precision,
    latent_eoy_transition_delta double precision,
    eoy_generation_mode text NOT NULL,
    eoy_transition_type text NOT NULL,
    eoy_academic_profile_status text NOT NULL,
    observed_growth_delta double precision,
    academic_profile_status text NOT NULL,
    PRIMARY KEY (school_year, sis_user_id)
);

CREATE TABLE analytics.fact_assessment_score (
    assessment_score_fact_id integer PRIMARY KEY,
    student_dim_id integer NOT NULL REFERENCES analytics.dim_student(student_dim_id),
    course_dim_id integer NOT NULL REFERENCES analytics.dim_course(course_dim_id),
    section_dim_id integer NOT NULL REFERENCES analytics.dim_section(section_dim_id),
    teacher_dim_id integer NOT NULL REFERENCES analytics.dim_teacher(teacher_dim_id),
    assignment_dim_id integer NOT NULL REFERENCES analytics.dim_assignment(assignment_dim_id),
    school_year text NOT NULL,
    school_year_offset integer NOT NULL,
    sis_user_id text NOT NULL,
    course_id text NOT NULL,
    section_id text NOT NULL,
    teacher_id text NOT NULL,
    assignment_label text NOT NULL,
    sequence_index integer NOT NULL,
    assessment_window text NOT NULL,
    expected_transition_type text NOT NULL,
    actual_transition_type text NOT NULL,
    generation_mode text NOT NULL,
    population_status text NOT NULL,
    score double precision NOT NULL,
    present_student_score double precision,
    potential_score double precision,
    posterior_readiness_after double precision,
    growth_delta double precision,
    latent_transition_type text NOT NULL,
    latent_readiness_before double precision,
    latent_readiness_after double precision NOT NULL,
    latent_transition_delta double precision,
    is_populated boolean NOT NULL,
    is_present boolean NOT NULL,
    is_nonparticipation_zero boolean NOT NULL,
    UNIQUE (school_year, sis_user_id, assignment_label)
);

CREATE TABLE analytics.fact_lms_enrollment (
    lms_enrollment_fact_id integer PRIMARY KEY,
    student_dim_id integer NOT NULL REFERENCES analytics.dim_student(student_dim_id),
    course_dim_id integer NOT NULL REFERENCES analytics.dim_course(course_dim_id),
    section_dim_id integer NOT NULL REFERENCES analytics.dim_section(section_dim_id),
    teacher_dim_id integer NOT NULL REFERENCES analytics.dim_teacher(teacher_dim_id),
    extraction_batch_id text NOT NULL,
    source_system text NOT NULL,
    school_year text NOT NULL,
    canvas_course_id text NOT NULL,
    course_id text NOT NULL,
    section_id text NOT NULL,
    teacher_id text NOT NULL,
    sis_user_id text NOT NULL,
    grade_level integer NOT NULL,
    enrollment_status text NOT NULL,
    is_active_enrollment boolean NOT NULL,
    reconciliation_status text NOT NULL,
    UNIQUE (school_year, sis_user_id)
);

CREATE TABLE analytics.validation_summary (
    check_name text PRIMARY KEY,
    observed_value text NOT NULL,
    expected_value text NOT NULL,
    status text NOT NULL
);

CREATE TABLE analytics.pipeline_runs (
    run_id text PRIMARY KEY,
    source_project text NOT NULL,
    loader_version text NOT NULL,
    source_commit text NOT NULL,
    table_counts jsonb NOT NULL,
    validation_status text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW public.course_section_performance AS
SELECT
    sr.school_year,
    sr.course_id,
    sr.course_name,
    sr.course_track,
    sr.section_id,
    sr.section_label,
    sr.teacher_id,
    sr.teacher_label,
    sr.boy_assignment_label AS assignment_label,
    'beginning_of_year'::text AS assessment_window,
    COUNT(*) AS enrolled_students,
    SUM(CASE WHEN sr.present_boy THEN 1 ELSE 0 END) AS present_students,
    ROUND((1 - AVG(CASE WHEN sr.present_boy THEN 1.0 ELSE 0.0 END))::numeric, 4) AS nonparticipation_rate,
    ROUND(AVG(CASE WHEN sr.present_boy THEN sr.boy_score ELSE NULL END)::numeric, 2) AS avg_present_score
FROM analytics.student_readiness AS sr
GROUP BY
    sr.school_year,
    sr.course_id,
    sr.course_name,
    sr.course_track,
    sr.section_id,
    sr.section_label,
    sr.teacher_id,
    sr.teacher_label,
    sr.boy_assignment_label
UNION ALL
SELECT
    sr.school_year,
    sr.course_id,
    sr.course_name,
    sr.course_track,
    sr.section_id,
    sr.section_label,
    sr.teacher_id,
    sr.teacher_label,
    sr.eoy_assignment_label AS assignment_label,
    'end_of_year'::text AS assessment_window,
    COUNT(*) AS enrolled_students,
    SUM(CASE WHEN sr.present_eoy THEN 1 ELSE 0 END) AS present_students,
    ROUND((1 - AVG(CASE WHEN sr.present_eoy THEN 1.0 ELSE 0.0 END))::numeric, 4) AS nonparticipation_rate,
    ROUND(AVG(CASE WHEN sr.present_eoy THEN sr.eoy_score ELSE NULL END)::numeric, 2) AS avg_present_score
FROM analytics.student_readiness AS sr
GROUP BY
    sr.school_year,
    sr.course_id,
    sr.course_name,
    sr.course_track,
    sr.section_id,
    sr.section_label,
    sr.teacher_id,
    sr.teacher_label,
    sr.eoy_assignment_label;

CREATE OR REPLACE VIEW public.assignment_growth_by_course AS
SELECT
    school_year,
    grade_level,
    course_id,
    course_name,
    course_track,
    COUNT(*) AS matched_students,
    ROUND(AVG(CASE WHEN present_boy THEN boy_score ELSE NULL END)::numeric, 2) AS boy_avg,
    ROUND(AVG(CASE WHEN present_eoy THEN eoy_score ELSE NULL END)::numeric, 2) AS eoy_avg,
    ROUND(AVG(observed_growth_delta)::numeric, 2) AS avg_observed_growth_delta
FROM analytics.student_readiness
GROUP BY
    school_year,
    grade_level,
    course_id,
    course_name,
    course_track;

CREATE OR REPLACE VIEW public.nonparticipation_by_group AS
SELECT
    school_year,
    boy_assignment_label AS assignment_label,
    grade_level,
    attendance_category,
    course_track,
    COUNT(*) AS student_assignment_rows,
    SUM(CASE WHEN NOT present_boy THEN 1 ELSE 0 END) AS nonparticipation_zero_rows,
    ROUND((1 - AVG(CASE WHEN present_boy THEN 1.0 ELSE 0.0 END))::numeric, 4) AS nonparticipation_rate
FROM analytics.student_readiness
GROUP BY
    school_year,
    boy_assignment_label,
    grade_level,
    attendance_category,
    course_track
UNION ALL
SELECT
    school_year,
    eoy_assignment_label AS assignment_label,
    grade_level,
    attendance_category,
    course_track,
    COUNT(*) AS student_assignment_rows,
    SUM(CASE WHEN NOT present_eoy THEN 1 ELSE 0 END) AS nonparticipation_zero_rows,
    ROUND((1 - AVG(CASE WHEN present_eoy THEN 1.0 ELSE 0.0 END))::numeric, 4) AS nonparticipation_rate
FROM analytics.student_readiness
GROUP BY
    school_year,
    eoy_assignment_label,
    grade_level,
    attendance_category,
    course_track;

CREATE OR REPLACE VIEW public.lms_enrollment_reconciliation AS
SELECT
    fle.school_year,
    fle.canvas_course_id,
    fle.course_id,
    dc.course_name,
    dc.course_track,
    fle.section_id,
    ds.section_label,
    fle.teacher_id,
    dt.teacher_label,
    fle.sis_user_id,
    st.student_label,
    fle.grade_level,
    fle.enrollment_status,
    fle.reconciliation_status
FROM analytics.fact_lms_enrollment AS fle
JOIN analytics.dim_course AS dc
    ON fle.course_dim_id = dc.course_dim_id
JOIN analytics.dim_section AS ds
    ON fle.section_dim_id = ds.section_dim_id
JOIN analytics.dim_teacher AS dt
    ON fle.teacher_dim_id = dt.teacher_dim_id
JOIN analytics.dim_student AS st
    ON fle.student_dim_id = st.student_dim_id;

CREATE OR REPLACE VIEW public.student_readiness_extract AS
SELECT
    school_year,
    sis_user_id,
    student_label,
    grade_level,
    course_id,
    course_name,
    course_track,
    section_id,
    section_label,
    teacher_id,
    teacher_label,
    attendance_category,
    attendance_probability,
    boy_assignment_label,
    eoy_assignment_label,
    boy_score,
    eoy_score,
    present_boy,
    present_eoy,
    observed_growth_delta,
    modeled_eoy_growth_delta,
    posterior_readiness_after_eoy,
    latent_readiness_after_boy,
    latent_readiness_after_eoy,
    latent_eoy_transition_delta,
    eoy_generation_mode,
    eoy_transition_type,
    academic_profile_status
FROM analytics.student_readiness;

COMMENT ON SCHEMA analytics IS 'Validated public-safe synthetic education analytics facts and dimensions.';
COMMENT ON SCHEMA lms IS 'Public-safe synthetic Canvas-style course and roster tables.';
