CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS raw_canvas;
CREATE SCHEMA IF NOT EXISTS mart;

DROP TABLE IF EXISTS raw.gradebook;
DROP TABLE IF EXISTS raw.students;
DROP TABLE IF EXISTS raw.school_years;
DROP TABLE IF EXISTS raw.teachers;
DROP TABLE IF EXISTS raw.courses;
DROP TABLE IF EXISTS raw.sections;
DROP TABLE IF EXISTS raw.enrollments;
DROP TABLE IF EXISTS raw.assignments;
DROP TABLE IF EXISTS raw.assessment_scores;
DROP TABLE IF EXISTS raw_canvas.courses;
DROP TABLE IF EXISTS raw_canvas.sections;
DROP TABLE IF EXISTS raw_canvas.enrollments;

DROP TABLE IF EXISTS mart.student_assessment_long;
DROP TABLE IF EXISTS mart.canvas_roster_sql_extract;
DROP TABLE IF EXISTS mart.student_readiness;
DROP TABLE IF EXISTS mart.assignment_growth;
DROP TABLE IF EXISTS mart.course_section_summary;
DROP TABLE IF EXISTS mart.missingness_attendance;
DROP TABLE IF EXISTS mart.teacher_section_effects;
DROP TABLE IF EXISTS mart.lms_to_sql_roster_reconciliation;
DROP TABLE IF EXISTS mart.canvas_course_pipeline_audit;
DROP TABLE IF EXISTS mart.fact_lms_enrollment;
DROP TABLE IF EXISTS mart.fact_assessment_score;
DROP TABLE IF EXISTS mart.dim_assignment;
DROP TABLE IF EXISTS mart.dim_teacher;
DROP TABLE IF EXISTS mart.dim_section;
DROP TABLE IF EXISTS mart.dim_course;
DROP TABLE IF EXISTS mart.dim_student;
DROP TABLE IF EXISTS mart.validation_summary;

CREATE TABLE raw.gradebook (
    student_label VARCHAR,
    export_id VARCHAR,
    sis_user_id VARCHAR,
    sis_login_id VARCHAR,
    email VARCHAR,
    canvas_gradebook_section VARCHAR,
    assignment_01 DOUBLE,
    assignment_02 DOUBLE,
    assignment_03 DOUBLE,
    assignment_04 DOUBLE,
    assignment_05 DOUBLE,
    assignment_06 DOUBLE,
    assignment_07 DOUBLE,
    assignment_08 DOUBLE,
    assignment_09 DOUBLE,
    assignment_10 DOUBLE,
    assignment_11 DOUBLE,
    assignment_12 DOUBLE,
    assignment_13 DOUBLE,
    assignment_14 DOUBLE
);

CREATE TABLE raw.students (
    sis_user_id VARCHAR,
    student_label VARCHAR,
    export_id VARCHAR,
    sis_login_id VARCHAR,
    email VARCHAR,
    canvas_gradebook_section VARCHAR,
    graduation_year INTEGER,
    graduation_year_suffix VARCHAR,
    cohort_label VARCHAR,
    entry_school_year VARCHAR,
    entry_school_year_offset INTEGER,
    graduation_school_year VARCHAR,
    graduation_school_year_offset INTEGER,
    attendance_category VARCHAR,
    attendance_probability DOUBLE,
    latest_academic_profile_status VARCHAR,
    latest_posterior_readiness DOUBLE,
    latest_latent_readiness DOUBLE,
    latest_present_score DOUBLE
);

CREATE TABLE raw.school_years (
    school_year VARCHAR,
    school_year_offset INTEGER,
    beginning_assignment_label VARCHAR,
    end_assignment_label VARCHAR,
    active_student_count INTEGER,
    new_freshman_count INTEGER,
    graduating_senior_count INTEGER,
    section_count INTEGER
);

CREATE TABLE raw.teachers (
    school_year VARCHAR,
    teacher_id VARCHAR,
    teacher_label VARCHAR,
    target_section_load INTEGER,
    teacher_growth_effect DOUBLE
);

CREATE TABLE raw.courses (
    course_id VARCHAR,
    course_name VARCHAR,
    track VARCHAR,
    sequence_order INTEGER,
    current_year_eligible BOOLEAN
);

CREATE TABLE raw.sections (
    school_year VARCHAR,
    school_year_offset INTEGER,
    section_id VARCHAR,
    course_id VARCHAR,
    section_label VARCHAR,
    teacher_id VARCHAR,
    teacher_label VARCHAR,
    period_label VARCHAR,
    target_enrollment INTEGER,
    max_capacity INTEGER,
    class_size_band VARCHAR,
    section_growth_effect DOUBLE,
    teacher_growth_effect DOUBLE
);

CREATE TABLE raw.enrollments (
    school_year VARCHAR,
    school_year_offset INTEGER,
    student_label VARCHAR,
    sis_user_id VARCHAR,
    grade_level INTEGER,
    course_id VARCHAR,
    section_id VARCHAR,
    teacher_id VARCHAR,
    enrollment_status VARCHAR
);

CREATE TABLE raw.assignments (
    assignment_label VARCHAR,
    sequence_index INTEGER,
    school_year VARCHAR,
    school_year_offset INTEGER,
    assessment_window VARCHAR,
    transition_type VARCHAR,
    population_status VARCHAR
);

CREATE TABLE raw.assessment_scores (
    school_year VARCHAR,
    school_year_offset INTEGER,
    assignment_label VARCHAR,
    sequence_index INTEGER,
    assessment_window VARCHAR,
    expected_transition_type VARCHAR,
    actual_transition_type VARCHAR,
    generation_mode VARCHAR,
    sis_user_id VARCHAR,
    student_label VARCHAR,
    grade_level INTEGER,
    course_id VARCHAR,
    course_track VARCHAR,
    section_id VARCHAR,
    teacher_id VARCHAR,
    attendance_category VARCHAR,
    attendance_probability DOUBLE,
    present BOOLEAN,
    observed_score DOUBLE,
    potential_score DOUBLE,
    posterior_readiness_after DOUBLE,
    growth_delta DOUBLE,
    latent_transition_type VARCHAR,
    latent_readiness_before DOUBLE,
    latent_readiness_after DOUBLE,
    latent_transition_delta DOUBLE,
    academic_profile_status VARCHAR
);

CREATE TABLE raw_canvas.courses (
    canvas_course_id VARCHAR,
    course_id VARCHAR,
    course_name VARCHAR,
    school_year VARCHAR,
    source_system VARCHAR,
    track VARCHAR,
    profile_path VARCHAR,
    extraction_batch_id VARCHAR
);

CREATE TABLE raw_canvas.sections (
    canvas_course_id VARCHAR,
    school_year VARCHAR,
    course_id VARCHAR,
    section_id VARCHAR,
    section_label VARCHAR,
    period_label VARCHAR,
    teacher_id VARCHAR,
    teacher_label VARCHAR,
    extraction_batch_id VARCHAR
);

CREATE TABLE raw_canvas.enrollments (
    canvas_course_id VARCHAR,
    school_year VARCHAR,
    course_id VARCHAR,
    section_id VARCHAR,
    sis_user_id VARCHAR,
    student_label VARCHAR,
    email VARCHAR,
    grade_level INTEGER,
    enrollment_status VARCHAR,
    extraction_batch_id VARCHAR
);
