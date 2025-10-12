# pages/dashboard.py

import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import yfinance as yf
from utils.data_handler import fetch_stock_data, get_key_metrics
from utils.ml_model import train_and_predict_svr
import pandas as pd

dash.register_page(__name__, path='/', name='Dashboard')

# Helper function to create a metric card
def create_metric_card(label, value, class_name=""):
    return html.Div([
        html.P(label, className="metric-card-label"),
        html.H5(value, className=f"metric-card-value {class_name}")
    ], className="metric-card")

layout = dbc.Container([
    dcc.Store(id='current-ticker-store', data=None),
    dbc.Row([dbc.Col(html.H2("AI Stock Analysis Dashboard"), width=12, className="mb-4 text-center")], align="center"),
    dbc.Row([
        dbc.Col(dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)", type="text"), width=9),
        dbc.Col(dbc.Button("Analyze Stock", id="analyze-button", color="primary", className="w-100"), width=3)
    ], className="mb-4"),
    html.Div(id="transaction-alert-placeholder"),
    dbc.Row([dbc.Col(dcc.Loading(id="loading-spinner", type="default", children=html.Div(id="dashboard-content")), width=12)]),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(html.P("Quantity:"), width=4),
                dbc.Col(dbc.Input(id="quantity-input", type="number", min=1, step=1, placeholder="Enter quantity..."), width=8),
            ]),
            html.P(id="transaction-summary", className="mt-3"),
        ]),
        dbc.ModalFooter(dbc.Button("Confirm", id="confirm-transaction-button", color="success")),
    ], id="transaction-modal", is_open=False)
], fluid=True, className="mt-4")

# This callback remains the same as Part 9
@callback(
    [Output("dashboard-content", "children"),
    Output("current-ticker-store", "data")],
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value"),
    prevent_initial_call=True
)
def update_dashboard(n_clicks, ticker):
    if not ticker:
        return html.Div("Please enter a stock ticker.", style={'textAlign': 'center'}), dash.no_update
    stock_data, stock_info = fetch_stock_data(ticker.upper())
    if stock_data is None:
        return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'.", color="danger"), dash.no_update
    metrics, change_color = get_key_metrics(stock_info, stock_data)
    predictions_df = train_and_predict_svr(stock_data, days_to_predict=10)
    fig = go.Figure(data=[go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Price')])
    if not predictions_df.empty:
        fig.add_trace(go.Scatter(x=predictions_df['Date'], y=predictions_df['Predicted_Close'], mode='lines', name='SVR Prediction', line=dict(color='#00BFFF', width=2, dash='dash')))
    fig.update_layout(title=f"{stock_info.get('longName', ticker.upper())} Price Chart & AI Forecast", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D')
    prediction_summary_text = f"The AI model predicts the price to be around {stock_info.get('currency', '')} {predictions_df['Predicted_Close'].iloc[0]:,.2f} tomorrow." if not predictions_df.empty else "Prediction data not available."
    content_layout = html.Div([
        html.Div([
            html.H3(stock_info.get('longName', ticker.upper())),
            html.H5(f"{stock_info.get('symbol')} | {stock_info.get('exchangeName')}", style={'color': '#a9a9a9'}),
            dbc.Row([dbc.Col(dbc.Button("Buy", id="buy-button", color="success", className="w-100"), width=6), dbc.Col(dbc.Button("Sell", id="sell-button", color="danger", className="w-100"), width=6)], className="mt-3")
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(create_metric_card("Current Price", metrics["Current Price"]), md=3),
            dbc.Col(create_metric_card("Price Change", metrics["Price Change"], class_name="positive-change" if change_color == 'green' else "negative-change"), md=3),
            dbc.Col(create_metric_card("Volume", metrics["Volume"]), md=3),
            dbc.Col(create_metric_card("Avg. Volume", metrics["Avg. Volume"]), md=3),
        ]),
        dbc.Card(dbc.CardBody([html.H5("AI Price Forecast"), html.P(prediction_summary_text)]), className="mt-4 mb-4"),
        dbc.Card(dcc.Graph(figure=fig))
    ])
    return content_layout, ticker.upper()

# This callback remains the same as Part 9
@callback(
    [Output("transaction-modal", "is_open"),
    Output("modal-title", "children"),
    Output("confirm-transaction-button", "color"),
    Output("confirm-transaction-button", "custom_data")],
    [Input("buy-button", "n_clicks"), Input("sell-button", "n_clicks")],
    prevent_initial_call=True
)
def open_transaction_modal(buy_clicks, sell_clicks):
    triggered_id = ctx.triggered_id
    if triggered_id == "buy-button": return True, "Buy Stock", "success", "BUY"
    if triggered_id == "sell-button": return True, "Sell Stock", "danger", "SELL"
    return False, "", "", ""

# --- UPDATED: Callback for executing transactions with brokerage fee logic ---
@callback(
    [Output("wallet-balance-store", "data"),
    Output("portfolio-store", "data"),
    Output("trading-history-store", "data"),
    Output("wallet-history-store", "data"), # NEW OUTPUT
    Output("transaction-alert-placeholder", "children"),
    Output("transaction-modal", "is_open", allow_duplicate=True)],
    Input("confirm-transaction-button", "n_clicks"),
    [State("confirm-transaction-button", "custom_data"),
    State("quantity-input", "value"),
    State("current-ticker-store", "data"),
    State("wallet-balance-store", "data"),
    State("portfolio-store", "data"),
    State("trading-history-store", "data"),
    State("wallet-history-store", "data")], # NEW STATE
    prevent_initial_call=True
)
def execute_transaction(n_clicks, trans_type, qty, ticker, balance, portfolio, trade_hist, wallet_hist):
    if not all([trans_type, qty, ticker]):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dbc.Alert("Invalid details.", color="warning"), False

    try:
        current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
        total_value = qty * current_price
        alert_msg, alert_color = "", "info"

        if trans_type == "BUY":
            if balance < total_value:
                return dash.no_update*4, dbc.Alert("Insufficient funds.", color="danger"), False
            balance -= total_value
            if ticker in portfolio:
                new_qty = portfolio[ticker]['quantity'] + qty
                new_avg = ((portfolio[ticker]['avg_price'] * portfolio[ticker]['quantity']) + total_value) / new_qty
                portfolio[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
            else:
                portfolio[ticker] = {'quantity': qty, 'avg_price': current_price}
            alert_msg, alert_color = f"Successfully purchased {qty} shares of {ticker}.", "success"

        elif trans_type == "SELL":
            if ticker not in portfolio or portfolio[ticker]['quantity'] < qty:
                return dash.no_update*4, dbc.Alert("Not enough shares to sell.", color="danger"), False

            # --- NEW: Profit and Brokerage Fee Logic ---
            cost_basis = portfolio[ticker]['avg_price'] * qty
            profit = total_value - cost_basis

            balance += total_value # Add full sale amount first

            if profit > 0:
                brokerage_fee = profit * 0.10
                balance -= brokerage_fee # Deduct fee from balance
                fee_record = {'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"Brokerage fee on {ticker} profit", 'Amount': f"-₹{brokerage_fee:,.2f}", 'Balance': f"₹{balance:,.2f}"}
                wallet_hist.append(fee_record)
                alert_msg = f"Sold {qty} shares of {ticker} for a profit of ₹{profit:,.2f}. A 10% brokerage fee (₹{brokerage_fee:,.2f}) was applied."
            else:
                alert_msg = f"Sold {qty} shares of {ticker}."

            portfolio[ticker]['quantity'] -= qty
            if portfolio[ticker]['quantity'] == 0:
                del portfolio[ticker]
            alert_color = "success"

        trade_record = {'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': trans_type, 'Quantity': qty, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_value:,.2f}"}
        trade_hist.append(trade_record)

        wallet_record = {'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"{trans_type} {ticker}", 'Amount': f"-₹{total_value:,.2f}" if trans_type == "BUY" else f"+₹{total_value:,.2f}", 'Balance': f"₹{balance:,.2f}"}
        wallet_hist.append(wallet_record)

        alert = dbc.Alert(alert_msg, color=alert_color, dismissable=True, duration=5000)
        return balance, portfolio, trade_hist, wallet_hist, alert, False

    except Exception as e:
        return dash.no_update*4, dbc.Alert(f"Transaction failed: {e}", color="danger"), False
