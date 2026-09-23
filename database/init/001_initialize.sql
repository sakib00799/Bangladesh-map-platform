\set ON_ERROR_STOP on

CREATE EXTENSION IF NOT EXISTS postgis;

\i /database/migrations/001_create_test_locations.sql
\i /database/migrations/002_convert_test_users_to_donors.sql
\i /database/migrations/003_remove_test_donors.sql
