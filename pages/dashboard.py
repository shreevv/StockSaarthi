# pages/dashboard.py
import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
from utils.data_handler import (
    fetch_stock_data, get_key_metrics, calculate_technical_indicators,
    fetch_news, fetch_corporate_actions
)
from utils.ml_model import train_and_predict_svr, generate_recommendation

dash.register_page(__name__, path='/', name='Dashboard')

def create_metric_card(label, value, class_name=""):
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.P(label, className="text-muted small mb-1"),
        html.H5(value, className=f"fw-bold {class_name}")
    ])), md=4)

layout = dbc.Container(fluid=True, children=[
    dcc.Store(id='current-ticker-store'),
    dcc.Store(id='current-recommendation-store'),
    html.H2("AI Stock Analysis Dashboard", className="text-center mb-4"),
    dbc.Row(justify="center", children=[
        dbc.Col(lg=6, md=8, children=[
            dbc.InputGroup([
                dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., RELIANCE.NS)"),
                dbc.Button("Analyze Stock", id="analyze-button", className="btn-primary"),
            ])
        ])
    ]),
    html.Div(id="alert-placeholder", className="mt-3"),
    dcc.Loading(html.Div(id="dashboard-content", className="mt-4")),
    
    # Modals
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(dbc.Input(id="quantity-input", type="number", min=1, placeholder="Enter quantity...")),
        dbc.ModalFooter(dbc.Button("Confirm", id="confirm-transaction-button"))
    ], id="transaction-modal", is_open=False),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Set Price Alert")),
        dbc.ModalBody([
            dbc.InputGroup([dbc.InputGroupText("Upper Target"), dbc.Input(id="upper-alert-input", type="number", min=0)], className="mb-3"),
            dbc.InputGroup([dbc.InputGroupText("Lower Target"), dbc.Input(id="lower-alert-input", type="number", min=0)]),
        ]),
        dbc.ModalFooter(dbc.Button("Set Alert", id="confirm-alert-button", className="btn-primary")),
    ], id="alert-modal", is_open=False),
])

# MAIN CALLBACK TO RENDER DASHBOARD (BUG-FIXED)
@callback(
    [Output("dashboard-content", "children"),
     Output("current-ticker-store", "data"),
     Output("current-recommendation-store", "data"),
     Output("alert-placeholder", "children")],
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value"),
    prevent_initial_call=True
)
def update_dashboard(n_clicks, ticker):
    if not ticker:
        return dash.no_update, dash.no_update, dash.no_update, dbc.Alert("Please enter a stock ticker.", color="warning")
    
    stock_data, stock_info = fetch_stock_data(ticker.upper())
    
    if stock_data is None:
        return dash.no_update, dash.no_update, dash.no_update, dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'. Please check the ticker symbol and try again.", color="danger")
    
    # --- Data Processing and Figure Generation ---
    stock_data_tech = calculate_technical_indicators(stock_data.copy())
    news = fetch_news(ticker.upper())
    dividends, splits = fetch_corporate_actions(ticker.upper())
    metrics, change_color_class = get_key_metrics(stock_info, stock_data)
    predictions_df = train_and_predict_svr(stock_data)
    reco = generate_recommendation(stock_data, predictions_df)
    
    # --- UI Components ---
    header_section = html.Div([
        html.H3(stock_info.get('longName', ticker.upper())),
        html.P(f"{stock_info.get('symbol')} | {stock_info.get('exchangeName')}", className="text-muted"),
        dbc.Row([
            dbc.Col(dbc.Button("Buy", id="buy-button", className="w-100 btn-success"), width="auto"),
            dbc.Col(dbc.Button("Sell", id="sell-button", className="w-100 btn-danger"), width="auto"),
            dbc.Col(dbc.Button("Add to Watchlist", id="watchlist-button", className="w-100 btn-secondary"), width="auto"),
            dbc.Col(dbc.Button("Set Price Alert", id="alert-button", className="w-100 btn-secondary"), width="auto"),
        ], className="mt-3 g-2")
    ], className="mb-4")

    ai_section = dbc.Card(dbc.CardBody([
        html.H4("AI Recommendation", className="text-center mb-4"),
        dbc.Row(justify="center", align="center", children=[
            create_metric_card("Recommendation", reco['recommendation']),
            create_metric_card("Risk Level", reco['risk']),
            create_metric_card("10-Day Target", f"₹{reco['target_price']}"),
        ]),
        html.Hr(className="my-4"),
        dbc.Row(justify="center", align="center", children=[
            dbc.Col(html.P("Enable automated trading for this recommendation:", className="mb-0"), width="auto"),
            dbc.Col(dbc.Switch(id="autotrade-switch", value=False, label="Auto-Trade"), width="auto"),
            html.Div(id="autotrade-status-output", className="small text-muted text-center mt-2")
        ])
    ]), className="mb-4")

    # --- Plotly Figures ---
    fig_price = go.Figure(data=[go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Price')])
    if not predictions_df.empty:
        fig_price.add_trace(go.Scatter(x=predictions_df['Date'], y=predictions_df['Predicted_Close'], mode='lines', name='AI Forecast', line=dict(color='#3498DB', width=2, dash='dash')))
    fig_price.update_layout(title="Price Chart & AI Forecast", template="plotly_white", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    # ... (other figures for RSI, MACD are the same) ...

    tabs_section = dbc.Tabs([...]) # As before, but ensure light theme
    
    layout = html.Div([header_section, ai_section, tabs_section])
    return layout, ticker.upper(), reco, None # Clear any previous alerts

# --- ALL OTHER CALLBACKS (Transactions, Watchlist, Alerts) REMAIN THE SAME ---
# --- NEW CALLBACK FOR AUTO-TRADE SWITCH ---
@callback(
    [Output("autotrade-store", "data"),
     Output("autotrade-status-output", "children")],
    Input("autotrade-switch", "value"),
    [State("current-ticker-store", "data"),
     State("current-recommendation-store", "data"),
     State("autotrade-store", "data")],
    prevent_initial_call=True
)
def update_autotrade_store(is_on, ticker, reco, auto_trades):
    if not ticker or not reco:
        return dash.no_update, ""
    
    auto_trades = auto_trades or {}
    
    if is_on:
        if reco['recommendation'] in ['Buy', 'Sell']:
            target_price = float(reco['target_price'].replace(',', ''))
            auto_trades[ticker] = {
                'type': reco['recommendation'].upper(),
                'target': target_price
            }
            status = f"Auto-trade armed. Will {reco['recommendation']} {ticker} at or near ₹{target_price}."
            return auto_trades, status
        else:
            status = "Auto-trade only available for 'Buy' or 'Sell' recommendations."
            return auto_trades, status
    else:
        if ticker in auto_trades:
            del auto_trades[ticker]
            status = "Auto-trade disarmed for this stock."
            return auto_trades, status
    
    return dash.no_update, ""
