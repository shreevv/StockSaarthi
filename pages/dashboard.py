# pages/dashboard.py
# (All imports remain the same as Part 13)
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

# The main layout and helper functions are unchanged from Part 13
# ...
# --- NOTE: The full layout is omitted for brevity. You must include your full layout from Part 13.
# The key change is inside the 'update_dashboard' callback's return value.

# The main dashboard update callback
@callback(
    # Outputs are the same
    [Output("dashboard-content", "children"), Output("current-ticker-store", "data")],
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value"),
    prevent_initial_call=True
)
def update_dashboard(n_clicks, ticker):
    if not ticker: return html.Div("Please enter a stock ticker."), dash.no_update
    # (Data fetching and figure creation logic is the same as Part 13)
    stock_data, stock_info = fetch_stock_data(ticker.upper())
    if stock_data is None: return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'.", color="danger"), dash.no_update
    stock_data = calculate_technical_indicators(stock_data)
    news_articles = fetch_news(ticker.upper())
    metrics, change_color = get_key_metrics(stock_info, stock_data)
    predictions_df = train_and_predict_svr(stock_data, days_to_predict=10)
    reco = generate_recommendation(stock_data, predictions_df)
    reco_color = {"Buy": "success", "Sell": "danger", "Hold": "secondary"}

    # --- NEW: Create the Auto-Trade Switch and its data ---
    autotrade_switch = dbc.Switch(
        id="autotrade-switch",
        label="Enable Automated Trading",
        value=False, # We need a callback to set this based on the store
        # Store recommendation data needed for the autotrade callback
        custom_data={'type': reco['recommendation'], 'target': float(reco['target_price'].replace(',', ''))}
    )

    # --- UPDATED: AI Recommendation Card with Auto-Trade Switch ---
    recommendation_card = dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.H4("AI Recommendation"), width=12, className="text-center mb-3"),
                dbc.Col(dbc.Button(reco['recommendation'], color=reco_color.get(reco['recommendation']), className="w-100 fw-bold"), md=4),
                dbc.Col(create_metric_card("Risk Level", reco['risk']), md=4),
                dbc.Col(create_metric_card(f"10-Day Target", f"{stock_info.get('currency', '')} {reco['target_price']}"), md=4)
            ]),
            # Add switch only for Buy/Sell recommendations
            html.Div(autotrade_switch, className="mt-3") if reco['recommendation'] in ["Buy", "Sell"] else ""
        ]), className="mb-4"
    )

    # --- NOTE: For your actual file, you must include the full logic for building the content_layout from Part 13 here.
    # This is a placeholder showing where the new recommendation card goes.
    full_content_layout = html.Div(["...Header, Buttons...", recommendation_card, "...Tabs with Charts and News..."])
    return full_content_layout, ticker.upper()

# --- NEW: Callback to update the auto-trade store when the switch is toggled ---
@callback(
    [Output("autotrade-store", "data"),
     Output("autotrade-switch", "value")],
    Input("autotrade-switch", "value"),
    [State("current-ticker-store", "data"),
     State("autotrade-switch", "custom_data"),
     State("autotrade-store", "data")]
)
def update_autotrade_jobs(switch_on, ticker, reco_data, auto_trades):
    if ticker is None or reco_data is None:
        return dash.no_update

    auto_trades = auto_trades or {}

    # This logic syncs the switch state with the store on page load
    if not ctx.triggered_id == "autotrade-switch":
         if ticker in auto_trades:
             return dash.no_update, True
         else:
             return dash.no_update, False

    # This logic runs when the user clicks the switch
    if switch_on:
        auto_trades[ticker] = reco_data
    else:
        if ticker in auto_trades:
            del auto_trades[ticker]

    return auto_trades, switch_on

# --- NOTE: The transaction callbacks and watchlist callbacks remain unchanged from previous parts. You must include their full code here. ---
# ... (open_transaction_modal callback) ...
# ... (execute_transaction callback) ...
# ... (update_watchlist callback) ...
