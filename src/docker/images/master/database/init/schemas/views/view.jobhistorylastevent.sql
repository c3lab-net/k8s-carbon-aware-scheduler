CREATE VIEW JobHistoryLastEvent
AS
    SELECT DISTINCT ON (job_id)
            job_id, event, time
        FROM JobHistory
        ORDER BY job_id, time DESC;
