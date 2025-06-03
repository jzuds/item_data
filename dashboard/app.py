import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import altair as alt  # Make sure this import is included at the top


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
            item_id,
            avg_high_price,
            high_price_volume,
            avg_low_price,
            low_price_volume,
            to_timestamp(event_unixtime) at time zone 'UTC' as event_unixtime,
            fetch_time
        FROM raw.raw_ge_history
        where item_id = 565
        ORDER BY event_unixtime DESC
        ;
    """)
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)
    return df

def main():
    st.title("GE History Viewer")
    st.write("High and Low Prices Over Time from `raw.raw_ge_history`:")

    engine = get_engine()
    try:
        df = load_sample_data(engine)

        # Check if required columns exist
        required_cols = ['event_unixtime', 'avg_high_price', 'avg_low_price']
        if all(col in df.columns for col in required_cols):
            price_df = df[required_cols].copy()
            price_df = price_df.sort_values(by='event_unixtime', ascending=False)


            # After creating `price_df`
            y_min = min(price_df[['avg_high_price', 'avg_low_price']].min())
            y_max = max(price_df[['avg_high_price', 'avg_low_price']].max())

            # Melt the dataframe to long format for Altair
            chart_df = price_df.melt(id_vars='event_unixtime', value_vars=['avg_high_price', 'avg_low_price'],
                                    var_name='Price Type', value_name='Price')

            # Create the Altair line chart
            chart = alt.Chart(chart_df).mark_line().encode(
                x='event_unixtime:T',
                y=alt.Y('Price:Q', scale=alt.Scale(domain=[y_min, y_max])),
                color='Price Type:N'
            ).properties(
                width=700,
                height=400,
                title="Average High and Low Prices Over Time"
            )

            st.altair_chart(chart, use_container_width=True)

            st.dataframe(price_df.head(12))

        else:
            st.warning(f"One or more required columns not found in the data: {required_cols}")

    except Exception as e:
        st.error(f"Error loading data: {e}")


if __name__ == "__main__":
    main()
