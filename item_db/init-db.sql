-- USERS
------------------------------------------------
------------------------------------------------
CREATE USER etl_user WITH PASSWORD 'password';
CREATE USER analytics_ro_user WITH PASSWORD 'password';

-- ROLE
------------------------------------------------
------------------------------------------------
CREATE ROLE etl_role;
CREATE ROLE analytics_ro_role;

GRANT etl_role TO etl_user;
GRANT analytics_ro_role TO analytics_ro_user;

-- SCHEMA
------------------------------------------------
------------------------------------------------
CREATE schema if not EXISTS raw;
CREATE SCHEMA if not exists transform;

GRANT USAGE ON SCHEMA raw TO etl_role;
GRANT USAGE ON SCHEMA raw TO analytics_ro_role;
GRANT USAGE ON SCHEMA transform TO etl_role;
GRANT USAGE ON SCHEMA transform TO analytics_ro_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO etl_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA transform TO etl_role;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO analytics_ro_role;
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
CREATE MATERIALIZED VIEW IF NOT EXISTS "transform"."ge_history" as
SELECT
  item_id,
  to_timestamp(event_unixtime) at time zone 'utc' AS event_timestamp,
  avg_high_price AS avg_high_price,
  coalesce(high_price_volume, 0) AS high_price_volume,
  (avg_high_price::BIGINT * high_price_volume::BIGINT) AS high_market_spend,
  avg_low_price AS avg_low_price,
  coalesce(low_price_volume, 0) AS low_price_volume,
  (avg_low_price::BIGINT * low_price_volume::BIGINT) AS low_market_spend,
  ROUND((
    coalesce(avg_high_price::BIGINT * high_price_volume::BIGINT, 0) +
    coalesce(avg_low_price::BIGINT * low_price_volume::BIGINT, 0)
  ) / nullif(coalesce(low_price_volume, 0) + coalesce(high_price_volume, 0), 0)::FLOAT)::BIGINT AS weighted_price,
  coalesce(low_price_volume, 0) + coalesce(high_price_volume, 0) AS total_volume,
  (coalesce(avg_high_price::BIGINT * high_price_volume::BIGINT, 0) + coalesce(avg_low_price::BIGINT * low_price_volume::BIGINT, 0)) AS total_market_spend
FROM raw.raw_ge_history
order by event_unixtime desc
;

-- INDEXES
------------------------------------------------
------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_raw_ge_history_item_id ON "raw"."raw_ge_history" (item_id);
CREATE INDEX IF NOT EXISTS idx_raw_ge_history_event_unixtime ON "raw"."raw_ge_history" (event_unixtime);
