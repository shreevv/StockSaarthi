# pages/dashboard.py

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from utils.data_handler import fetch_stock_data, get_key_metrics

dash.register_page(__name__, path='/', name='Dashboard')

# Helper function to create a metric card
def create_metric_card(label, value, class_name=""):
    return html.Div(
        [
            html.P(label, className="metric-card-label"),
            html.H5(value, className=f"metric-card-value {class_name}")
        ],
        className="metric-card"
    )

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("AI Stock Analysis Dashboard"), width=12, className="mb-4 text-center"),
    ], align="center"),
    
    dbc.Row([
        dbc.Col(dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)", type="text"), width=9),
        dbc.Col(dbc.Button("Analyze Stock", id="analyze-button", color="primary", className="w-100"), width=3)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(
            dcc.Loading(
                id="loading-spinner",
                type="default",
                children=html.Div(id="dashboard-content")
            )
        , width=12)
    ])
], fluid=True, className="mt-4")

@callback(
    Output("dashboard-content", "children"),
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value")
)
def update_dashboard(n_clicks, ticker):
    if n_clicks is None or not ticker:
        return html.Div("Please enter a stock ticker and click 'Analyze'.", style={'textAlign': 'center', 'marginTop': '2rem'})

    stock_data, stock_info = fetch_stock_data(ticker.upper())

    if stock_data is None:
        return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'. Please check the ticker and try again.", color="danger")

    # Get Metrics and Chart
    metrics, change_color = get_key_metrics(stock_info, stock_data)

    fig = go.Figure(data=[go.Candlestick(
        x=stock_data.index, open=stock_data['Open'], high=stock_data['High'],
        low=stock_data['Low'], close=stock_data['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name=ticker.upper()
    )])
    
    fig.update_layout(
        title=f"{stock_info.get('longName', ticker.upper())} Price Chart",
        template="plotly_dark", xaxis_rangeslider_visible=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D',
        font=dict(family="Lato, sans-serif", color="white")
    )
    
    # Build the Layout with Metrics and Chart
    content_layout = html.Div([
        # Stock Header
        html.Div([
            html.H3(stock_info.get('longName', ticker.upper())),
            html.H5(f"{stock_info.get('symbol')} | {stock_info.get('exchangeName')}", style={'color': '#a9a9a9'}),
        ], className="mb-4"),
        
        # Row 1 of Metrics
        dbc.Row([
            dbc.Col(create_metric_card("Current Price", metrics["Current Price"]), width=3),
            dbc.Col(create_metric_card("Price Change", metrics["Price Change"], 
                                       class_name="positive-change" if change_color == 'green' else "negative-change"), width=3),
            dbc.Col(create_metric_card("Volume", metrics["Volume"]), width=3),
            dbc.Col(create_metric_card("Avg. Volume", metrics["Avg. Volume"]), width=3),
        ]),
        
        # Row 2 of Metrics
        dbc.Row([
            dbc.Col(create_metric_card("52-Week High", metrics["52-Week High"]), width=3),
            dbc.Col(create_metric_card("52-Week Low", metrics["52-Week Low"]), width=3),
            dbc.Col(create_metric_card("Market Cap", metrics["Market Cap"]), width=3),
            dbc.Col(create_metric_card("P/E Ratio", metrics["P/E Ratio"]), width=3),
        ]),
        
        # Chart
        dbc.Card(dcc.Graph(figure=fig), className="mt-4")
    ])

    return content_layout