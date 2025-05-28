-- Create table for item data
CREATE TABLE IF NOT EXISTS item_data (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    avg_high_price INTEGER,
    high_price_volume INTEGER,
    avg_low_price INTEGER,
    low_price_volume INTEGER,
    timestamp BIGINT,
    fetch_time TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT unique_item_timestamp UNIQUE (item_id, timestamp)
);

-- Add indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_item_data_item_id ON item_data (item_id);
CREATE INDEX IF NOT EXISTS idx_item_data_timestamp ON item_data (timestamp);
CREATE INDEX IF NOT EXISTS idx_item_data_fetch_time ON item_data (fetch_time);


-- Analytical views

drop view item_change_analysis;

-- Create table for item data
CREATE TABLE IF NOT EXISTS item_data (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    avg_high_price INTEGER,
    high_price_volume INTEGER,
    avg_low_price INTEGER,
    low_price_volume INTEGER,
    timestamp BIGINT,
    fetch_time TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT unique_item_timestamp UNIQUE (item_id, timestamp)
);

-- Add indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_item_data_item_id ON item_data (item_id);
CREATE INDEX IF NOT EXISTS idx_item_data_timestamp ON item_data (timestamp);
CREATE INDEX IF NOT EXISTS idx_item_data_fetch_time ON item_data (fetch_time);


-- Analytical views
CREATE OR REPLACE VIEW item_change_analysis AS
WITH base AS (
    SELECT 
        item_id,
        avg_high_price,
        avg_low_price,
        high_price_volume,
        low_price_volume,
        (high_price_volume + low_price_volume) AS total_volume,
        (avg_high_price - avg_low_price) AS avg_price_margin,
        (low_price_volume * avg_low_price) + (high_price_volume * avg_high_price) AS total_market_spend,
        (low_price_volume * avg_low_price) + (high_price_volume * avg_high_price) AS total_market_margin,
        TO_TIMESTAMP("timestamp") AT TIME ZONE 'EST' AS event_timestamp_est,
        TO_TIMESTAMP("timestamp") AT TIME ZONE 'UTC' AS event_timestamp_utc,
        "timestamp" AS timestamp_number
    FROM item_data
)

SELECT
    item_id,
    avg_high_price,
    avg_low_price,
    avg_price_margin,
    high_price_volume,
    low_price_volume,
    total_volume,
    event_timestamp_est,
    event_timestamp_utc,
    timestamp_number,
    total_market_spend,
    total_market_margin,

    SUM(total_market_spend) OVER (
        PARTITION BY item_id 
        ORDER BY timestamp_number ASC
    ) AS total_market_spend_accum,

    SUM(total_market_spend) OVER (
        PARTITION BY item_id  
        ORDER BY event_timestamp_utc 
        RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
    ) AS total_market_spend_accum_1h,

    SUM(total_volume) OVER (
        PARTITION BY item_id  
        ORDER BY event_timestamp_utc 
        RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
    ) AS total_volume_accum_1h,

    avg_high_price 
        - FIRST_VALUE(avg_high_price) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND INTERVAL '5 minutes' PRECEDING
        ) AS avg_high_price_change_5m,

    avg_high_price 
        - FIRST_VALUE(avg_high_price) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND INTERVAL '30 minutes' PRECEDING
        ) AS avg_high_price_change_30m,

    avg_high_price 
        - FIRST_VALUE(avg_high_price) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND INTERVAL '60 minutes' PRECEDING
        ) AS avg_high_price_change_60m,

    high_price_volume 
        - FIRST_VALUE(high_price_volume) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND INTERVAL '5 minutes' PRECEDING
        ) AS high_price_volume_change_5m,

    high_price_volume 
        - FIRST_VALUE(high_price_volume) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND INTERVAL '30 minutes' PRECEDING
        ) AS high_price_volume_change_30m,

    high_price_volume 
        - FIRST_VALUE(high_price_volume) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND INTERVAL '60 minutes' PRECEDING
        ) AS high_price_volume_change_60m,

    avg_low_price 
        - FIRST_VALUE(avg_low_price) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND INTERVAL '5 minutes' PRECEDING
        ) AS avg_low_price_change_5m,

    avg_low_price 
        - FIRST_VALUE(avg_low_price) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND INTERVAL '30 minutes' PRECEDING
        ) AS avg_low_price_change_30m,

    avg_low_price 
        - FIRST_VALUE(avg_low_price) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND INTERVAL '60 minutes' PRECEDING
        ) AS avg_low_price_change_60m,

    low_price_volume 
        - FIRST_VALUE(low_price_volume) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND INTERVAL '5 minutes' PRECEDING
        ) AS low_price_volume_change_5m,

    low_price_volume 
        - FIRST_VALUE(low_price_volume) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND INTERVAL '30 minutes' PRECEDING
        ) AS low_price_volume_change_30m,

    low_price_volume 
        - FIRST_VALUE(low_price_volume) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND INTERVAL '60 minutes' PRECEDING
        ) AS low_price_volume_change_60m,

    avg_price_margin 
        - FIRST_VALUE(avg_price_margin) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND INTERVAL '5 minutes' PRECEDING
        ) AS avg_price_margin_change_5m,

    avg_price_margin 
        - FIRST_VALUE(avg_price_margin) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND INTERVAL '30 minutes' PRECEDING
        ) AS avg_price_margin_change_30m,

    avg_price_margin 
        - FIRST_VALUE(avg_price_margin) OVER (
            PARTITION BY item_id 
            ORDER BY event_timestamp_utc 
            RANGE BETWEEN INTERVAL '60 minutes' PRECEDING AND INTERVAL '60 minutes' PRECEDING
        ) AS avg_price_margin_change_60m,

    DATE_TRUNC('day', event_timestamp_est)::DATE AS event_date_est,
    DATE_TRUNC('hour', event_timestamp_est)::TIMESTAMP AS event_time_est,
    CASE 
        when TO_CHAR(DATE_TRUNC('hour', event_timestamp_est)::TIMESTAMP, 'MM') = '00'
        then 1
        ELSE 0
    END AS top_of_the_hour_flag

FROM base

ORDER BY 
    item_id ASC,
    timestamp_number ASC;