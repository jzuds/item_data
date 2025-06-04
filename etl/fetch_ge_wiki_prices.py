import argparse
import time
from datetime import datetime
import os
from dotenv import load_dotenv, find_dotenv
import requests

from sqlalchemy import (
    create_engine, Column, Integer, Numeric, TIMESTAMP, MetaData, Table, func
)
from sqlalchemy.orm import sessionmaker

# Load .env file
load_dotenv(find_dotenv())

def fetch_api_data(api_unixtime: int):
    headers = {"User-Agent": os.getenv("USER_AGENT", "ItemDataCollector/1.0")}
    url = f"https://prices.runescape.wiki/api/v1/osrs/5m?timestamp={api_unixtime}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        json_data = response.json()
        data = json_data.get("data", {})
        timestamp = json_data.get("timestamp")

        if not data:
            # Calculate how old the requested timestamp is
            request_time = datetime.fromtimestamp(api_unixtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            age = now - request_time

            if age > timedelta(hours=6):
                print(f"No data for timestamp {api_unixtime}, and it's older than 6 hour. Skipping gracefully.")
                sys.exit(0)  # Graceful exit — Airflow will treat this as success
            else:
                raise ValueError("API response contains no data, but timestamp is recent.")

        if timestamp is None:
            raise ValueError("API response missing 'timestamp' field.")

        print(f"timestamp={timestamp} count={len(data)}")
        return data, timestamp

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        raise
    except ValueError as e:
        print(f"Data parsing error: {e}")
        raise




def get_raw_price_data_table(metadata):
    return Table(
        'raw_ge_history', metadata,
        Column('item_id', Integer, primary_key=False, nullable=False),
        Column('avg_high_price', Integer, nullable=True),
        Column('high_price_volume', Integer, nullable=True),
        Column('avg_low_price', Integer, nullable=True),
        Column('low_price_volume', Integer, nullable=True),
        Column('event_unixtime', Integer, nullable=False),
        Column('fetch_time', TIMESTAMP(timezone=True), nullable=False),
        schema='raw'
    )


from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime, timezone

def insert_data(session, table, data, event_unixtime):
    fetch_time = datetime.now(timezone.utc)

    try:
        for item_id_str, values in data.items():
            item_id = int(item_id_str)
            row = {
                'item_id': item_id,
                'avg_high_price': values.get('avgHighPrice'),
                'high_price_volume': values.get('highPriceVolume'),
                'avg_low_price': values.get('avgLowPrice'),
                'low_price_volume': values.get('lowPriceVolume'),
                'event_unixtime': event_unixtime,
                'fetch_time': fetch_time
            }

            stmt = pg_insert(table).values(**row).on_conflict_do_nothing()
            session.execute(stmt)

        session.commit()
        print(f"Inserted data for {len(data)} items at event_unixtime={event_unixtime}")

    except Exception as e:
        session.rollback()
        print(f"Error inserting data: {e}")



def main():
    parser = argparse.ArgumentParser(description="Fetch API data and insert into PostgreSQL.")
    parser.add_argument('unixtimestamp', type=int, help='Unix timestamp of the API call')

    args = parser.parse_args()
    api_unixtime = args.unixtimestamp

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL must be set in .env file")

    response = fetch_api_data(api_unixtime)

    data, api_timestamp_unix = fetch_api_data(api_unixtime)
    if api_timestamp_unix is None:
        raise ValueError("API response missing 'timestamp'")

    engine = create_engine(db_url)
    metadata = MetaData()
    raw_price_data = get_raw_price_data_table(metadata)
    Session = sessionmaker(bind=engine)
    session = Session()

    insert_data(session, raw_price_data, data, api_timestamp_unix)

    session.close()


if __name__ == "__main__":
    main()
