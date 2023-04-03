CREATE TABLE JobConfig(
    job_id UUID NOT NULL REFERENCES JobRequest(job_id),
    job_config jsonb NOT NULL
)
