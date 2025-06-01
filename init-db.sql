-- USERS
------------------------------------------------
------------------------------------------------
CREATE USER etl_user WITH PASSWORD 'password';
CREATE USER readonly_user WITH PASSWORD 'password';

-- ROLE
------------------------------------------------
------------------------------------------------
CREATE ROLE etl_role;
CREATE ROLE analytics_ro_user;

GRANT etl_role TO etl_user;
GRANT analytics_ro_role TO analytics_ro_user;

-- SCHEMA
------------------------------------------------
------------------------------------------------
CREATE schema if not EXISTS raw;
CREATE SCHEMA if not exists transform;

GRANT USAGE ON SCHEMA raw TO etl_role;
GRANT USAGE ON SCHEMA transform TO etl_role;
GRANT USAGE ON SCHEMA transform TO analytics_ro_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO etl_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA transform TO etl_role;
GRANT SELECT ON ALL TABLES IN SCHEMA transform TO analytics_ro_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA "raw"
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA "transform"
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA transform
  GRANT SELECT ON TABLES TO analytics_ro_role;


-- TABLES
------------------------------------------------
------------------------------------------------
CREATE TABLE IF NOT EXISTS "raw"."raw_ge_history" (
    item_id INTEGER NOT NULL,
    avg_high_price INTEGER,
    high_price_volume INTEGER,
    avg_low_price INTEGER,
    low_price_volume INTEGER,
    event_unixtime BIGINT,
    fetch_time TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT unique_item_event UNIQUE (item_id, event_unixtime)
);

-- VIEWS
------------------------------------------------
------------------------------------------------

-- INDEXES
------------------------------------------------
------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_raw_ge_history_item_id ON "raw"."raw_ge_history" (item_id);
CREATE INDEX IF NOT EXISTS idx_raw_ge_history_event_unixtime ON "raw"."raw_ge_history" (event_unixtime);
