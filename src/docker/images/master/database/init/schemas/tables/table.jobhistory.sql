CREATE TABLE JobHistory(
    job_id UUID NOT NULL REFERENCES JobRequest(job_id),
    event VARCHAR(16) NOT NULL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT job_history_unique_job_id_event UNIQUE (job_id, event)
)
