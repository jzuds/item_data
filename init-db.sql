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


-- Analytical views
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