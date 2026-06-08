CREATE OR REPLACE TABLE mart.dim_course AS
SELECT
    ROW_NUMBER() OVER (ORDER BY c.sequence_order, c.course_id) AS course_dim_id,
    c.course_id,
    c.course_name,
    c.track AS course_track,
    c.sequence_order,
    c.current_year_eligible
FROM raw.courses AS c;
