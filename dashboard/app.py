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
        WITH hourly_agg AS (
            SELECT
                item_id,
                date_trunc('hour', to_timestamp(event_unixtime) AT TIME ZONE 'UTC') AS event_hourly_utc,
                ROUND(
                    SUM((avg_low_price) * (low_price_volume)) 
                    / NULLIF(SUM(low_price_volume), 0)
                ) AS avgw_hourly_low_price,
                ROUND(
                    SUM((avg_high_price) * (high_price_volume)) 
                    / NULLIF(SUM(high_price_volume), 0)
                ) AS avgw_hourly_high_price
            FROM raw.raw_ge_history
            WHERE item_id = 565
            GROUP BY item_id, date_trunc('hour', to_timestamp(event_unixtime) AT TIME ZONE 'UTC')
            ORDER BY date_trunc('hour', to_timestamp(event_unixtime) AT TIME ZONE 'UTC') DESC
        )
        SELECT
            item_id,
            event_hourly_utc,
            event_hourly_utc AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York' as event_hourly_est,
            avgw_hourly_low_price,
            avgw_hourly_high_price
        FROM hourly_agg
        ;

    """)
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)
    return df.reset_index(drop=True)

def main():
    st.title("GE History Viewer")
    st.write("High and Low Prices Over Time from `raw.raw_ge_history`:")

    engine = get_engine()
    try:
        df = load_sample_data(engine)

        # Check if required columns exist
        required_cols = ['event_hourly_est', 'avgw_hourly_low_price', 'avgw_hourly_high_price']
        if all(col in df.columns for col in required_cols):
            price_df = df[required_cols].copy()
            price_df = price_df.sort_values(by='event_hourly_est', ascending=False)


            # After creating `price_df`
            y_min = min(price_df[['avgw_hourly_high_price', 'avgw_hourly_low_price']].min())
            y_max = max(price_df[['avgw_hourly_high_price', 'avgw_hourly_low_price']].max())

            # Melt the dataframe to long format for Altair
            chart_df = price_df.melt(id_vars='event_hourly_est', value_vars=['avgw_hourly_high_price', 'avgw_hourly_low_price'],
                                    var_name='Price Type', value_name='Price')

            # Create the Altair line chart
            chart = alt.Chart(chart_df).mark_line().encode(
                x='event_hourly_est:T',
                y=alt.Y('Price:Q', scale=alt.Scale(domain=[y_min, y_max])),
                color='Price Type:N'
            ).properties(
                width=700,
                height=400,
                title="Average High and Low Prices Over Time"
            )

            st.altair_chart(chart, use_container_width=True)

            st.dataframe(price_df.head(24))

        else:
            st.warning(f"One or more required columns not found in the data: {required_cols}")

    except Exception as e:
        st.error(f"Error loading data: {e}")


if __name__ == "__main__":
    main()
