CREATE OR REPLACE TABLE mart.dim_assignment AS
SELECT
    ROW_NUMBER() OVER (ORDER BY a.sequence_index) AS assignment_dim_id,
    a.assignment_label,
    a.sequence_index,
    a.school_year,
    a.school_year_offset,
    a.assessment_window,
    a.transition_type,
    a.population_status
FROM raw.assignments AS a;
