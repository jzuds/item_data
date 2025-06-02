import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Create SQLAlchemy engine
def get_engine():
    db_url = (os.getenv('DATABASE_URL'))
    return create_engine(db_url)

# Load sample data using SQLAlchemy
def load_sample_data(engine):
    query = text("""
        SELECT 
            * 
        FROM raw.raw_ge_history
        where item_id = 565
        ORDER BY fetch_time DESC
        LIMIT 10;
    """)
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)
    return df

# Streamlit UI
def main():
    st.title("GE History Viewer")
    st.write("Preview of the `raw.raw_ge_history` table:")

    engine = get_engine()
    try:
        df = load_sample_data(engine)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error loading data: {e}")

if __name__ == "__main__":
    main()
