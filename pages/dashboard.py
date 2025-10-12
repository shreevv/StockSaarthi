# pages/dashboard.py

import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import yfinance as yf
from utils.data_handler import fetch_stock_data, get_key_metrics
# --- NEW: Import the recommendation function ---
from utils.ml_model import train_and_predict_svr, generate_recommendation
import pandas as pd

dash.register_page(__name__, path='/', name='Dashboard')

def create_metric_card(label, value, class_name=""):
    return html.Div([html.P(label, className="metric-card-label"), html.H5(value, className=f"metric-card-value {class_name}")], className="metric-card")

layout = dbc.Container([
    dcc.Store(id='current-ticker-store', data=None),
    html.H2("AI Stock Analysis Dashboard", className="mb-4 text-center"),
    dbc.Row([
        dbc.Col(dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)", type="text"), width=9),
        dbc.Col(dbc.Button("Analyze Stock", id="analyze-button", color="primary", className="w-100"), width=3)
    ], className="mb-4"),
    html.Div(id="transaction-alert-placeholder"),
    dbc.Row([dbc.Col(dcc.Loading(id="loading-spinner", type="default", children=html.Div(id="dashboard-content")), width=12)]),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody([dbc.Row([dbc.Col(html.P("Quantity:"), width=4), dbc.Col(dbc.Input(id="quantity-input", type="number", min=1, step=1), width=8)])]),
        dbc.ModalFooter(dbc.Button("Confirm", id="confirm-transaction-button")),
    ], id="transaction-modal", is_open=False)
], fluid=True, className="mt-4")

@callback(
    Output("dashboard-content", "children"),
    Output("current-ticker-store", "data"),
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value"),
    prevent_initial_call=True
)
def update_dashboard(n_clicks, ticker):
    if not ticker:
        return html.Div("Please enter a stock ticker."), dash.no_update

    stock_data, stock_info = fetch_stock_data(ticker.upper())
    if stock_data is None:
        return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'.", color="danger"), dash.no_update

    metrics, change_color = get_key_metrics(stock_info, stock_data)
    predictions_df = train_and_predict_svr(stock_data, days_to_predict=10)
    # --- NEW: Generate recommendation ---
    reco = generate_recommendation(stock_data, predictions_df)
    reco_color = {"Buy": "success", "Sell": "danger", "Hold": "secondary"}

    fig = go.Figure(data=[go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Price')])
    if not predictions_df.empty:
        fig.add_trace(go.Scatter(x=predictions_df['Date'], y=predictions_df['Predicted_Close'], mode='lines', name='SVR Prediction', line=dict(color='#00BFFF', width=2, dash='dash')))
    fig.update_layout(title=f"{stock_info.get('longName', ticker.upper())} Price Chart & AI Forecast", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D')

    content_layout = html.Div([
        html.Div([
            html.H3(stock_info.get('longName', ticker.upper())),
            html.H5(f"{stock_info.get('symbol')} | {stock_info.get('exchangeName')}", style={'color': '#a9a9a9'}),
            dbc.Row([dbc.Col(dbc.Button("Buy", id="buy-button", color="success", className="w-100"), width=6), dbc.Col(dbc.Button("Sell", id="sell-button", color="danger", className="w-100"), width=6)], className="mt-3")
        ], className="mb-4"),

        # --- NEW: AI Recommendation Card ---
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.H4("AI Recommendation"), width=12, className="text-center"),
                    dbc.Col(
                        dbc.Button(reco['recommendation'], color=reco_color.get(reco['recommendation']), className="w-100 fw-bold"),
                        width=4,
                    ),
                    dbc.Col(create_metric_card("Risk Level", reco['risk']), width=4),
                    dbc.Col(create_metric_card(f"10-Day Target", f"{stock_info.get('currency', '')} {reco['target_price']}"), width=4)
                ])
            ]), className="mb-4"
        ),

        dbc.Row([
            dbc.Col(create_metric_card("Current Price", metrics["Current Price"]), md=3),
            dbc.Col(create_metric_card("Price Change", metrics["Price Change"], class_name="positive-change" if change_color == 'green' else "negative-change"), md=3),
            dbc.Col(create_metric_card("Volume", metrics["Volume"]), md=3),
            dbc.Col(create_metric_card("Avg. Volume", metrics["Avg. Volume"]), md=3),
        ]),
        dbc.Card(dcc.Graph(figure=fig), className="mt-4")
    ])
    return content_layout, ticker.upper()

# The two transaction callbacks below remain the same as Part 10.
# [Callback to open transaction modal]
@callback(
    [Output("transaction-modal", "is_open"), Output("modal-title", "children"), Output("confirm-transaction-button", "color"), Output("confirm-transaction-button", "custom_data")],
    [Input("buy-button", "n_clicks"), Input("sell-button", "n_clicks")],
    prevent_initial_call=True
)
def open_transaction_modal(buy_clicks, sell_clicks):
    triggered_id = ctx.triggered_id
    if triggered_id == "buy-button": return True, "Buy Stock", "success", "BUY"
    if triggered_id == "sell-button": return True, "Sell Stock", "danger", "SELL"
    return False, "", "", ""

# [Callback to execute transaction]
@callback(
    [Output("wallet-balance-store", "data"), Output("portfolio-store", "data"), Output("trading-history-store", "data"), Output("wallet-history-store", "data"), Output("transaction-alert-placeholder", "children"), Output("transaction-modal", "is_open", allow_duplicate=True)],
    Input("confirm-transaction-button", "n_clicks"),
    [State("confirm-transaction-button", "custom_data"), State("quantity-input", "value"), State("current-ticker-store", "data"), State("wallet-balance-store", "data"), State("portfolio-store", "data"), State("trading-history-store", "data"), State("wallet-history-store", "data")],
    prevent_initial_call=True
)
def execute_transaction(n_clicks, trans_type, qty, ticker, balance, portfolio, trade_hist, wallet_hist):
    if not all([trans_type, qty, ticker]): return (dash.no_update,) * 4 + (dbc.Alert("Invalid details.", color="warning"), False)
    try:
        current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
        total_value = qty * current_price
        if trans_type == "BUY":
            if balance < total_value: return (dash.no_update,) * 4 + (dbc.Alert("Insufficient funds.", color="danger"), False)
            balance -= total_value
            if ticker in portfolio:
                new_qty = portfolio[ticker]['quantity'] + qty
                new_avg = ((portfolio[ticker]['avg_price'] * portfolio[ticker]['quantity']) + total_value) / new_qty
                portfolio[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
            else:
                portfolio[ticker] = {'quantity': qty, 'avg_price': current_price}
            alert_msg, alert_color = f"Purchased {qty} shares of {ticker}.", "success"
        elif trans_type == "SELL":
            if ticker not in portfolio or portfolio[ticker]['quantity'] < qty: return (dash.no_update,) * 4 + (dbc.Alert("Not enough shares.", color="danger"), False)
            cost_basis = portfolio[ticker]['avg_price'] * qty
            profit = total_value - cost_basis
            balance += total_value
            if profit > 0:
                brokerage_fee = profit * 0.10
                balance -= brokerage_fee
                wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"Brokerage fee on {ticker} profit", 'Amount': f"-₹{brokerage_fee:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                alert_msg = f"Sold {qty} shares of {ticker} for a profit of ₹{profit:,.2f}. Fee of ₹{brokerage_fee:,.2f} applied."
            else:
                alert_msg = f"Sold {qty} shares of {ticker}."
            portfolio[ticker]['quantity'] -= qty
            if portfolio[ticker]['quantity'] == 0: del portfolio[ticker]
            alert_color = "success"
        trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': trans_type, 'Quantity': qty, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_value:,.2f}"})
        wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"{trans_type} {ticker}", 'Amount': f"-₹{total_value:,.2f}" if trans_type == "BUY" else f"+₹{total_value:,.2f}", 'Balance': f"₹{balance:,.2f}"})
        return balance, portfolio, trade_hist, wallet_hist, dbc.Alert(alert_msg, color=alert_color, dismissable=True, duration=5000), False
    except Exception as e:
        return (dash.no_update,) * 4 + (dbc.Alert(f"Transaction failed: {e}", color="danger"), False)
