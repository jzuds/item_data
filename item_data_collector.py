import argparse
import requests
import psycopg2
import json
import time
import datetime
from psycopg2.extras import RealDictCursor

# Constants
INTERVAL_SECONDS = 600  # 10 minutes
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5
USER_AGENT = "ItemDataCollector/1.0 (zudsgaming@gmail.com)"  # Replace with your contact info

# Database configuration
DB_CONFIG = {
    "dbname": "item_data_db",
    "user": "item_data_user",
    "password": "secure_password_123",  # Replace with your password
    "host": "localhost",
    "port": "5432"
}

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch OSRS item data.")
    parser.add_argument(
        "--item_id",
        type=int,
        required=True,
        help="Fetch data for a specific item ID (must be > 0)"
    )
    args = parser.parse_args()
    if args.item_id <= 0:
        parser.error("--item_id must be an integer greater than 0")
    return args

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def fetch_item_data(item_id: int):
    api_url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id={item_id}"
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for row in data["data"]:
                results.append({
                    "item_id": item_id,
                    "avg_high_price": row.get("avgHighPrice", 0),
                    "high_price_volume": row.get("highPriceVolume", 0),
                    "avg_low_price": row.get("avgLowPrice", 0),
                    "low_price_volume": row.get("lowPriceVolume", 0),
                    "timestamp": row.get("timestamp"),
                    "fetch_time": datetime.datetime.now().isoformat()
                })

            if not results:
                print(f"No data returned for item {item_id}")
            return results

        except (requests.RequestException, ValueError) as e:
            print(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS} failed: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY_SECONDS)
    print(f"Failed to fetch data for item {item_id} after {RETRY_ATTEMPTS} attempts.")
    return []

def insert_data_to_db(data_list):
    if not data_list:
        return

    conn = get_db_connection()
    if not conn:
        return

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
                    except psycopg2.Error as e:
                        print(f"DB insert error for item {data['item_id']}: {e}")
        print(f"Inserted {len(data_list)} entries successfully.")
    except psycopg2.Error as e:
        print(f"Database operation failed: {e}")
    finally:
        conn.close()

def main():
    args = parse_args()
    item_id = args.item_id
    print(f"Fetching data for item ID {item_id} every {INTERVAL_SECONDS} seconds...")

    while True:
        try:
            data_list = fetch_item_data(item_id)
            insert_data_to_db(data_list)
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("User interrupted. Exiting...")
            break
        except Exception as e:
            print(f"Unhandled error: {e}. Retrying in {INTERVAL_SECONDS} seconds...")
            time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
