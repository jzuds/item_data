import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import altair as alt

# Load environment variables
load_dotenv()

def get_engine():
    db_url = os.getenv('DATABASE_URL')
    return create_engine(db_url)

def load_sample_data(engine):
    query = text("""
    SELECT 
        item_id,
        event_timestamp,
        avg_high_price,
        high_price_volume,
        high_market_spend,
        avg_low_price,
        low_price_volume,
        low_market_spend,
        weighted_price,
        total_volume,
        total_market_spend,
        sum(total_volume) OVER (
                PARTITION BY item_id
                ORDER BY event_timestamp
                RANGE BETWEEN INTERVAL '1 day' PRECEDING AND CURRENT ROW
        )                                   as trailing_one_day_total_volume,
        (avg_high_price - avg_low_price) 	as high_low_margin,
        (avg_high_price - weighted_price) 	as high_weighted_margin,
        (weighted_price - avg_low_price) 	as weighted_low_margin,
        ROUND(
            AVG(avg_high_price - avg_low_price) OVER (
                PARTITION BY item_id
                ORDER BY event_timestamp
                RANGE BETWEEN INTERVAL '1 day' PRECEDING AND CURRENT ROW
            ), 2
        ) AS one_day_avg_high_low_margin
    FROM "transform".ge_history
    WHERE item_id = 565
    ORDER BY event_timestamp DESC;
    """)
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)
    return df.reset_index(drop=True)

def main():
    st.title("GE History Viewer")
    engine = get_engine()

    try:
        df = load_sample_data(engine)

        # High/low price chart
        st.header("1. Average High vs Low Prices Over Time")
        price_df = df[['event_timestamp', 'avg_high_price', 'avg_low_price']].sort_values(by='event_timestamp')
        chart_df = price_df.melt(id_vars='event_timestamp', value_vars=['avg_high_price', 'avg_low_price'],
                                 var_name='Price Type', value_name='Price')
        price_min = price_df[['avg_high_price', 'avg_low_price']].min().min()
        price_max = price_df[['avg_high_price', 'avg_low_price']].max().max()
        price_range = [price_min * 0.95, price_max * 1.05]  # ±5% buffer
        chart = alt.Chart(chart_df).mark_line().encode(
            x='event_timestamp:T',
            y=alt.Y('Price:Q', scale=alt.Scale(domain=price_range)),
            color='Price Type:N'
        ).properties(
            width=700,
            height=400
        )

        st.altair_chart(chart, use_container_width=True)

        # Volume Chart
        st.header("Volume: Accumulative 1D Total")
        vol_df = df[['event_timestamp', 'trailing_one_day_total_volume']].sort_values(by='event_timestamp')
        vol_df = vol_df.melt(id_vars='event_timestamp', value_vars=['trailing_one_day_total_volume'],
                             var_name='Volume Type', value_name='Volume')

        vol_chart = alt.Chart(vol_df).mark_area(opacity=0.6).encode(
            x='event_timestamp:T',
            y=alt.Y('Volume:Q'),
            color='Volume Type:N'
        ).properties(width=700, height=300)

        st.altair_chart(vol_chart, use_container_width=True)

        # One-day rolling average margin
        st.header("24H Avg High-Low Margin")
        roll_chart = alt.Chart(df.sort_values(by='event_timestamp')).mark_line(color='green').encode(
            x='event_timestamp:T',
            y='one_day_avg_high_low_margin:Q'
        ).properties(width=700, height=250)
        st.altair_chart(roll_chart, use_container_width=True)

        # Show data
        st.subheader("Raw Data Snapshot")
        st.dataframe(df.head(24))

    except Exception as e:
        st.error(f"Error loading data: {e}")

if __name__ == "__main__":
    main()
