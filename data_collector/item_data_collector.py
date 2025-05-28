import requests
import psycopg2
import json
import time
import datetime
import os
from pathlib import Path
from filelock import FileLock
from psycopg2.extras import RealDictCursor

# Configuration
CONFIG_FILE = Path("config.json")
QUEUE_DIR = Path("queue")
QUEUE_FILE = QUEUE_DIR / "item_data_queue.json"
LOCK_FILE = QUEUE_DIR / "item_data_queue.lock"
INTERVAL_SECONDS = 600  # 10 minutes
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5
USER_AGENT = "ItemDataCollector/1.0 (zudsgaming@gmail.com)"  # Replace with your contact info

# PostgreSQL connection settings
DB_CONFIG = {
    "dbname": "item_data_db",
    "user": "item_data_user",
    "password": "secure_password_123",  # Replace with your password
    "host": "localhost",
    "port": "5432"
}

def ensure_queue_dir():
    """Ensure the queue directory exists."""
    QUEUE_DIR.mkdir(exist_ok=True)

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def fetch_item_data(item_id:int):
    """Fetch trade volume and price data for all items from the OSRS Wiki API.
    https://prices.runescape.wiki/osrs/
    https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices
    """

    api_url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id=565"
    headers = {"User-Agent": USER_AGENT}
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            
            for row in data["data"]:
                results.append({
                    "item_id": int(item_id),
                    "avg_high_price": row.get("avgHighPrice", 0),
                    "high_price_volume": row.get("highPriceVolume", 0),
                    "avg_low_price": row.get("avgLowPrice", 0),
                    "low_price_volume": row.get("lowPriceVolume", 0),
                    "timestamp": row.get("timestamp"),
                    "fetch_time": datetime.datetime.now().isoformat()
                })
            
            if not results:
                print(f"Warning: No data returned for items at {datetime.datetime.now()}")
            return results
        
        except (requests.RequestException, ValueError) as e:
            print(f"Error on attempt {attempt + 1}/{RETRY_ATTEMPTS}: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"Failed to fetch data after {RETRY_ATTEMPTS} attempts")
                return []

def insert_data_to_db(data_list):
    """Insert fetched data into the PostgreSQL database. Return successful entries."""
    if not data_list:
        return []
    
    conn = get_db_connection()
    if not conn:
        return []
    
    successful = []
    try:
        with conn:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO item_data (
                        item_id, avg_high_price, high_price_volume,
                        avg_low_price, low_price_volume, timestamp, fetch_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (item_id, timestamp) DO NOTHING
                """
                for data in data_list:
                    values = (
                        data["item_id"],
                        data["avg_high_price"],
                        data["high_price_volume"],
                        data["avg_low_price"],
                        data["low_price_volume"],
                        data["timestamp"],
                        data["fetch_time"]
                    )
                    try:
                        cur.execute(query, values)
                        successful.append(data)
                    except psycopg2.Error as e:
                        print(f"Error inserting data for {data['item_id']}: {e}")
                print(f"Completing processing for {len(data)} entries at {datetime.datetime.now().isoformat()}")
        return successful
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def append_to_queue(data_list):
    """Append data to the queue file with file locking."""
    if not data_list:
        return
    
    ensure_queue_dir()
    lock = FileLock(LOCK_FILE)
    
    with lock:
        # Read existing queue or initialize empty list
        queue_data = []
        if QUEUE_FILE.exists():
            try:
                with QUEUE_FILE.open("r") as f:
                    queue_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Corrupted queue file. Starting fresh.")
        
        # Append new data
        queue_data.extend(data_list)
        
        # Write back to file
        try:
            with QUEUE_FILE.open("w") as f:
                json.dump(queue_data, f, indent=2)
            for data in data_list:
                print(f"Queued data for {data['name']} (ID {data['item_id']}) at {data['fetch_time']}")
        except IOError as e:
            print(f"Error writing to queue file: {e}")

def main():
    """Run the data collection loop."""    
    print(f"Fetching data every {INTERVAL_SECONDS} seconds...")
    
    ITEM_ID = 565
    ensure_queue_dir()
    
    while True:
        try:
            data_list = fetch_item_data(ITEM_ID)
            if data_list:
                successful = insert_data_to_db(data_list)
                # Queue any data that failed to insert
                failed = [data for data in data_list if data not in successful]
                if failed:
                    append_to_queue(failed)
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nStopped by user. Exiting...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in {INTERVAL_SECONDS} seconds...")
            time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()