# pages/dashboard.py

import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from utils.data_handler import fetch_stock_data, get_key_metrics, calculate_technical_indicators, fetch_news
from utils.ml_model import train_and_predict_svr, generate_recommendation
import pandas as pd

dash.register_page(__name__, path='/', name='Dashboard')

# The main layout structure is mostly the same, just with the new button
layout = dbc.Container([
    dcc.Store(id='current-ticker-store', data=None),
    html.H2("AI Stock Analysis Dashboard", className="mb-4 text-center"),
    dbc.Row([
        dbc.Col(dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker...", type="text"), width=9),
        dbc.Col(dbc.Button("Analyze Stock", id="analyze-button", color="primary", className="w-100"), width=3)
    ], className="mb-4"),
    html.Div(id="transaction-alert-placeholder"),
    html.Div(id="watchlist-alert-placeholder"), # NEW: For watchlist alerts
    dbc.Row([dbc.Col(dcc.Loading(children=html.Div(id="dashboard-content")), width=12)]),
    # The transaction modal remains unchanged
    dbc.Modal([dbc.ModalHeader(dbc.ModalTitle(id="modal-title")), dbc.ModalBody(dbc.Input(id="quantity-input", type="number", min=1)), dbc.ModalFooter(dbc.Button("Confirm", id="confirm-transaction-button"))], id="transaction-modal", is_open=False)
], fluid=True, className="mt-4")

# The main dashboard update callback is largely the same
@callback(
    [Output("dashboard-content", "children"),
     Output("current-ticker-store", "data")],
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value"),
    prevent_initial_call=True
)
def update_dashboard(n_clicks, ticker):
    if not ticker: return html.Div("Please enter a stock ticker."), dash.no_update
    stock_data, stock_info = fetch_stock_data(ticker.upper())
    if stock_data is None: return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'.", color="danger"), dash.no_update
    # (This section is the same as Part 13, creating figures and content)
    # ... for brevity, the full logic for building charts and tabs is not repeated here ...
    # --- NOTE: For your actual file, you must include the full logic for building the content_layout from Part 13 here. ---
    # The key addition is the watchlist button in the header
    header_buttons = dbc.Row([
        dbc.Col(dbc.Button("Buy", id="buy-button", color="success", className="w-100"), width=4),
        dbc.Col(dbc.Button("Sell", id="sell-button", color="danger", className="w-100"), width=4),
        dbc.Col(dbc.Button("Add to Watchlist", id="watchlist-button", color="info", outline=True, className="w-100"), width=4), # NEW
    ], className="mt-3")
    # You would then integrate this `header_buttons` into your `content_layout`
    # For a complete working file, please refer to the final consolidated code if needed.
    # This is a placeholder to show where the new button goes.
    full_content_layout = html.Div(["...Your full dashboard layout from Part 13...", header_buttons, "...Rest of the layout..."])
    return full_content_layout, ticker.upper()


# --- NEW: Callback to add/remove from watchlist ---
@callback(
    [Output("watchlist-store", "data"),
     Output("watchlist-alert-placeholder", "children"),
     Output("watchlist-button", "children"),
     Output("watchlist-button", "outline")],
    Input("watchlist-button", "n_clicks"),
    [State("current-ticker-store", "data"),
     State("watchlist-store", "data")],
    prevent_initial_call=True
)
def update_watchlist(n_clicks, ticker, watchlist):
    if not ticker: return dash.no_update

    watchlist = watchlist or []

    if ticker in watchlist:
        watchlist.remove(ticker)
        alert = dbc.Alert(f"{ticker} removed from your watchlist.", color="warning", duration=3000)
        button_text = "Add to Watchlist"
        outline = True
    else:
        watchlist.append(ticker)
        alert = dbc.Alert(f"{ticker} added to your watchlist.", color="success", duration=3000)
        button_text = "On Watchlist"
        outline = False

    return watchlist, alert, button_text, outline

# --- NOTE: The transaction callbacks remain unchanged from Part 13. You must include their full code here. ---
# ... (open_transaction_modal callback) ...
# ... (execute_transaction callback) ...
