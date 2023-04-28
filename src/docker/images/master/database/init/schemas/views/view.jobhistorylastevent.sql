CREATE VIEW JobHistoryLastEvent
AS
    SELECT DISTINCT ON (job_id)
            job_id, event, time, origin
        FROM JobHistory
        ORDER BY job_id, time DESC;
