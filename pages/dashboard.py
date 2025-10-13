# pages/dashboard.py

import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from utils.data_handler import (
    fetch_stock_data, get_key_metrics, calculate_technical_indicators,
    fetch_news, fetch_corporate_actions
)
from utils.ml_model import train_and_predict_svr, generate_recommendation
import pandas as pd

dash.register_page(__name__, path='/', name='Dashboard')

def create_metric_card(label, value, class_name=""):
    return html.Div([
        html.P(label, className="metric-card-label"),
        html.H5(value, className=f"metric-card-value {class_name}")
    ], className="metric-card")

layout = html.Main([
    dcc.Store(id='current-ticker-store', data=None),
    html.H2("AI Stock Analysis Dashboard", className="mb-4 text-center"),
    html.Form([
        dbc.Row([
            dbc.Col(dcc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)", type="text", name="ticker"), width=8, lg=9),
            dbc.Col(html.Button("Analyze Stock", id="analyze-button", n_clicks=0, className="btn btn-primary w-100"), width=4, lg=3)
        ])
    ], action="#", method="get"),
    html.Div(id="transaction-alert-placeholder"),
    html.Div(id="watchlist-alert-placeholder"),
    html.Section(id="dashboard-content"),
    # ... (rest of the layout remains the same)
])
# ... (callbacks remain the same)
