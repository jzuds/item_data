import os
from dotenv import load_dotenv
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import psycopg2
import plotly.graph_objs as go
import datetime
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Configuration
CONFIG = {
    'UPDATE_INTERVAL': 120000,  # 2 minutes in milliseconds
    'DEFAULT_ITEM_ID': 565,
    'TIME_RANGES': [
        {'label': 'Last 6 hours', 'value': 'Last 6 hours'},
        {'label': 'Last 12 hours', 'value': 'Last 12 hours'},
        {'label': 'Last day', 'value': 'Last day'},
        {'label': 'Last 7 days', 'value': 'Last 7 days'},
    ],
    'TICK_INTERVALS': {
        'Last 6 hours': 6,
        'Last 12 hours': 12,
        'Last day': 48,
        'Last 7 days': 96
    },
    'CACHE_TTL': 30,
}

# PostgreSQL connection setup
def get_data(selected_time_range=None):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "item_data_db"),
        user=os.getenv("DB_USER", "item_data_user"),
        password=os.getenv("DB_PASSWORD", "secure_password_123")
    )

    query = """
        SELECT 
            item_id,
            avg_high_price,
            avg_high_price_change_5m,
            avg_high_price_change_30m,
            avg_high_price_change_60m,
            high_price_volume,
            low_price_volume,
            total_volume,
            total_volume_accum_1h,
            total_market_spend,
            total_market_spend_accum_1h,
            total_market_margin,
            avg_low_price,
            avg_low_price_change_5m,
            avg_low_price_change_30m,
            avg_low_price_change_60m,
            avg_price_margin,
            avg_price_margin_change_5m,
            avg_price_margin_change_30m,
            avg_price_margin_change_60m,
            event_date_est,
            event_time_est,
            event_timestamp_est,
            event_timestamp_utc,
            timestamp_number
        FROM public.item_change_analysis
    """

    if selected_time_range:
        now = datetime.datetime.now()
        if selected_time_range == 'Last 6 hours':
            start_time = now - datetime.timedelta(hours=6)
        elif selected_time_range == 'Last 12 hours':
            start_time = now - datetime.timedelta(hours=12)
        elif selected_time_range == 'Last day':
            start_time = now - datetime.timedelta(days=1)
        elif selected_time_range == 'Last 7 days':
            start_time = now - datetime.timedelta(days=7)

        time_rounded_down_bottom_of_hour = start_time.replace(minute=0, second=0, microsecond=0)
        query += f" WHERE event_timestamp_utc >= '{time_rounded_down_bottom_of_hour}'"

    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Dash app setup
app = dash.Dash(__name__)
app.title = "Item Price Analysis"

app.layout = html.Div([
    html.H1("Item Price Analysis"),
    html.Div([
        html.Div([
            html.Label("Select Time Range:"),
            dcc.Dropdown(
                id='time-range-dropdown',
                options=CONFIG['TIME_RANGES'],
                value='Last day',
                style={'width': '100%'}
            )
        ], style={'width': '48%'}),
        html.Div([
            html.Label("Select Item ID:"),
            dcc.Dropdown(
                id='item-dropdown',
                options=[],
                value=CONFIG['DEFAULT_ITEM_ID'],
                style={'width': '100%'}
            )
        ], style={'width': '48%'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}),

    dcc.Interval(id='interval-component', interval=CONFIG['UPDATE_INTERVAL'], n_intervals=0),

    dcc.Graph(id='total-spend-graph'),
    dcc.Graph(id='high-low-price-graph'),
    dcc.Graph(id='high-low-volume-graph'),
    #dcc.Graph(id='margin-price-graph'),
])

@app.callback(
    [Output('item-dropdown', 'options'),
     Output('item-dropdown', 'value'),
     Output('total-spend-graph', 'figure'),
     Output('high-low-price-graph', 'figure'),
     Output('high-low-volume-graph', 'figure'),
     #Output('margin-price-graph', 'figure')
    ],
    [Input('interval-component', 'n_intervals'),
     Input('time-range-dropdown', 'value'),
     Input('item-dropdown', 'value')]
)
def update_graph(n, selected_time_range, selected_item_id):
    df = get_data(selected_time_range)

    available_item_ids = sorted(df['item_id'].unique())
    item_options = [{'label': str(item_id), 'value': item_id} for item_id in available_item_ids]

    if selected_item_id is None:
        selected_item_id = CONFIG['DEFAULT_ITEM_ID']

    df_filtered = df[df['item_id'] == selected_item_id]
    timestamps = df_filtered['event_timestamp_est']
    
    if not timestamps.empty:
        tick_interval = CONFIG['TICK_INTERVALS'].get(selected_time_range, 1)
        tick_indices = np.arange(0, len(timestamps), tick_interval)
        tickvals = timestamps.iloc[tick_indices]
        ticktext = tickvals.dt.strftime('%Y-%m-%d %H:%M')
    else:
        tickvals = []
        ticktext = []
    
    total_spend_trace = [
        go.Scatter(
            x=timestamps,
            y=df_filtered['total_market_spend'],
            mode='lines+markers',
            name='Market Spend',
            line=dict(color='orange', width=1)
        ),
        go.Scatter(
            x=timestamps,
            y=df_filtered['total_market_spend_accum_1h'],
            mode='lines+markers',
            name='1h Market Spend',
            line=dict(color='blue', width=1)
        )
    ]
    total_spend_layout = go.Layout(
        title=f'Total Market Spend ({selected_time_range}, Item: {selected_item_id})',
        xaxis=dict(title='Time', tickangle=45, tickvals=tickvals, ticktext=ticktext, automargin=True),
        yaxis=dict(title='GP'),
        height=400
    )

    high_start = df_filtered['avg_high_price'].iloc[0] if not df_filtered.empty else None
    low_start = df_filtered['avg_low_price'].iloc[0] if not df_filtered.empty else None

    high_low_price_traces = [
        go.Scatter(x=timestamps, y=df_filtered['avg_high_price'], name='Average High Price',
                   mode='lines+markers', line=dict(color='blue', width=1)),
        go.Scatter(x=timestamps, y=df_filtered['avg_low_price'], name='Average Low Price',
                   mode='lines+markers', line=dict(color='orange', width=1))
    ]
    if high_start is not None:
        high_low_price_traces.append(
            go.Scatter(x=[timestamps.min(), timestamps.max()], y=[high_start, high_start],
                       mode='lines', name='Start High Price',
                       line=dict(dash='dash', color='rgba(0, 102, 204, 0.5)')))
    if low_start is not None:
        high_low_price_traces.append(
            go.Scatter(x=[timestamps.min(), timestamps.max()], y=[low_start, low_start],
                       mode='lines', name='Start Low Price',
                       line=dict(dash='dash', color='rgba(255, 165, 0, 0.5)')))

    # Extract ending values (assuming timestamps are sorted chronologically)
    high_end = df_filtered['avg_high_price'].iloc[-1] if not df_filtered.empty else None
    low_end = df_filtered['avg_low_price'].iloc[-1] if not df_filtered.empty else None

    # Example: Define market start price (if you have it)
    market_start_price = df_filtered['market_price'].iloc[0] if 'market_price' in df_filtered.columns and not df_filtered.empty else None

    annotations = []

    # Add annotation for end high price
    if high_end is not None:
        annotations.append(dict(
            x=timestamps.iloc[-1],
            y=high_end,
            xref='x',
            yref='y',
            text=f'High End: {high_end} ({high_end - high_start})',
            showarrow=True,
            arrowhead=3,
            arrowwidth=1,
            ax=0,
            ay=-60
        ))

    # Add annotation for end low price
    if low_end is not None:
        annotations.append(dict(
            x=timestamps.iloc[-1],
            y=low_end,
            xref='x',
            yref='y',
            text=f'Low End: {low_end} ({low_end - low_start})',
            showarrow=True,
            arrowhead=3,
            arrowwidth=1,
            ax=0,
            ay=60
        ))

    # Apply to layout
    high_low_layout_prices = go.Layout(
        title=f'High/Low Prices ({selected_time_range}, Item: {selected_item_id})',
        xaxis=dict(title='Time', tickangle=45, tickvals=tickvals, ticktext=ticktext, automargin=True),
        yaxis=dict(title='GP'),
        height=400,
        annotations=annotations
    )


    high_low_volume_traces = [
        go.Scatter(x=timestamps, y=df_filtered['total_volume'], name='Market Volume',
                   mode='lines+markers', line=dict(color='orange')),
        go.Scatter(x=timestamps, y=df_filtered['total_volume_accum_1h'], name='1h Market Volume',
                   mode='lines+markers', line=dict(color='blue')),
    ]
    high_low_layout_volume = go.Layout(
        title=f'Volume Trends ({selected_time_range}, Item: {selected_item_id})',
        xaxis=dict(title='Time', tickangle=45, tickvals=tickvals, ticktext=ticktext, automargin=True),
        yaxis=dict(title='Volume'),
        height=400
    )

    # margin_colors = [
    #     'green' if val >= 0 else 'red'
    #     for val in df_filtered['avg_price_margin_change_5m']
    # ]
    # margin_changes = df_filtered['avg_price_margin_change_5m']

    # price_traces = [
    #     go.Bar(x=timestamps, y=df_filtered['avg_price_margin'], name='Price Margin',
    #            marker=dict(color='rgba(55, 83, 109, 0.7)')),
    #     go.Bar(x=timestamps, y=margin_changes, name='Trailing Margin Change',
    #            marker=dict(color=margin_colors))
    # ]
    # price_layout = go.Layout(
    #     title=f'Price Margin Analysis ({selected_time_range}, Item: {selected_item_id})',
    #     xaxis=dict(title='Time', tickangle=45, tickvals=tickvals, ticktext=ticktext, automargin=True),
    #     yaxis=dict(title='Margin'),
    #     barmode='overlay',
    #     height=400
    # )

    return item_options, selected_item_id, {
        'data': total_spend_trace, 'layout': total_spend_layout
    }, {
        'data': high_low_price_traces, 'layout': high_low_layout_prices
    }, {
        'data': high_low_volume_traces, 'layout': high_low_layout_volume
    } 
    # ,{
    #     'data': price_traces, 'layout': price_layout
    # }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
