#!/bin/sh

cd "$(dirname "$0")"

(set -x; pg_isready) || { echo >&2 "Failed to connect to database. Aborting ..."; exit 1; }

set -e
set -x

psql -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'

# Order matters
psql -v ON_ERROR_STOP=1 -f ./schemas/tables/table.jobrequest.sql
psql -v ON_ERROR_STOP=1 -f ./schemas/tables/table.jobconfig.sql
psql -v ON_ERROR_STOP=1 -f ./schemas/tables/table.jobhistory.sql

find ./schemas/indices -iname "*.sql" -exec psql -v ON_ERROR_STOP=1 -f {} \;
find ./schemas/views -iname "*.sql" -exec psql -v ON_ERROR_STOP=1 -f {} \;
