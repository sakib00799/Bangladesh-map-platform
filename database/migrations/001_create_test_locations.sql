CREATE TABLE IF NOT EXISTS test_locations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_locations_location_gist
    ON test_locations
    USING GIST (location);
