import psycopg2
import json
import time
import datetime
from pathlib import Path
from filelock import FileLock
from psycopg2.extras import RealDictCursor

# Configuration
INTERVAL_SECONDS = 60  # Check queue every 60 seconds
QUEUE_DIR = Path("queue")
QUEUE_FILE = QUEUE_DIR / "item_data_queue.json"
LOCK_FILE = QUEUE_DIR / "item_data_queue.lock"

# PostgreSQL connection settings
DB_CONFIG = {
    "dbname": "item_data_db",
    "user": "item_data_user",
    "password": "secure_password_123",  # Replace with your password
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def insert_data_to_db(data):
    """Insert data into the PostgreSQL database. Return True if successful."""
    conn = get_db_connection()
    if not conn:
        return False
    
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
                values = (
                    data["item_id"],
                    data["avg_high_price"],
                    data["high_price_volume"],
                    data["avg_low_price"],
                    data["low_price_volume"],
                    data["timestamp"],
                    data["fetch_time"]
                )
                cur.execute(query, values)
        print(f"Processed queue entry for (ID {data['item_id']}) from {data['fetch_time']}")
        return True
    except psycopg2.Error as e:
        print(f"Error inserting queue data for {data['item_id']}: {e}")
        return False
    finally:
        conn.close()

def process_queue():
    """Process all entries in the queue file and update the file."""
    if not QUEUE_FILE.exists():
        return 0
    
    lock = FileLock(LOCK_FILE)
    processed_count = 0
    
    with lock:
        # Read queue
        try:
            with QUEUE_FILE.open("r") as f:
                queue_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading queue file: {e}")
            return 0
        
        # Process entries
        remaining_data = []
        for data in queue_data:
            if not insert_data_to_db(data):
                remaining_data.append(data)  # Keep unprocessed entries
            else:
                processed_count += 1
        
        # Write back remaining entries
        try:
            if remaining_data:
                with QUEUE_FILE.open("w") as f:
                    json.dump(remaining_data, f, indent=2)
            else:
                QUEUE_FILE.unlink()  # Remove file if empty
        except IOError as e:
            print(f"Error writing to queue file: {e}")
    
    return processed_count

def main():
    """Run the queue processing loop."""
    print("Starting queue processor for item data...")
    print(f"Checking queue every {INTERVAL_SECONDS} seconds...")
    
    while True:
        try:
            processed = process_queue()
            if processed > 0:
                print(f"Processed {processed} queue entries at {datetime.datetime.now()}")
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nStopped by user. Exiting...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in {INTERVAL_SECONDS} seconds...")
            time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()