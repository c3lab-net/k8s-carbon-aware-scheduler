CREATE TABLE JobRequest (
    job_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    image VARCHAR(128) NOT NULL,
    command VARCHAR(1024) NOT NULL,
    max_delay INTERVAL DEFAULT INTERVAL '0'
)
