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
    return html.Div([html.P(label, className="metric-card-label"), html.H5(value, className=f"metric-card-value {class_name}")], className="metric-card")

layout = dbc.Container([
    dcc.Store(id='current-ticker-store', data=None),
    html.H2("AI Stock Analysis Dashboard", className="mb-4 text-center"),
    dbc.Row([
        dbc.Col(dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)", type="text"), width=8, lg=9),
        dbc.Col(dbc.Button("Analyze Stock", id="analyze-button", color="primary", className="w-100"), width=4, lg=3)
    ], className="mb-4"),
    html.Div(id="transaction-alert-placeholder"),
    html.Div(id="watchlist-alert-placeholder"),
    dbc.Row([dbc.Col(dcc.Loading(children=html.Div(id="dashboard-content")), width=12)]),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(dbc.Input(id="quantity-input", type="number", min=1, placeholder="Enter quantity...")),
        dbc.ModalFooter(dbc.Button("Confirm", id="confirm-transaction-button"))
    ], id="transaction-modal", is_open=False),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Set Price Alert")),
        dbc.ModalBody([
            dbc.Row([dbc.Col(html.P("Upper Target (> Current):"), width=6), dbc.Col(dbc.Input(id="upper-alert-input", type="number", min=0), width=6)], className="mb-3"),
            dbc.Row([dbc.Col(html.P("Lower Target (< Current):"), width=6), dbc.Col(dbc.Input(id="lower-alert-input", type="number", min=0), width=6)]),
        ]),
        dbc.ModalFooter(dbc.Button("Set Alert", id="confirm-alert-button", color="primary")),
    ], id="alert-modal", is_open=False),
], fluid=True, className="mt-4")

@callback(
    [Output("dashboard-content", "children"), Output("current-ticker-store", "data")],
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value"),
    prevent_initial_call=True
)
def update_dashboard(n_clicks, ticker):
    if not ticker: return html.Div("Please enter a stock ticker and click 'Analyze'."), dash.no_update
    stock_data, stock_info = fetch_stock_data(ticker.upper())
    if stock_data is None: return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'. Please check the ticker.", color="danger"), dash.no_update
    
    stock_data_tech = calculate_technical_indicators(stock_data.copy())
    news = fetch_news(ticker.upper())
    dividends, splits = fetch_corporate_actions(ticker.upper())
    metrics, change_color = get_key_metrics(stock_info, stock_data)
    predictions_df = train_and_predict_svr(stock_data)
    reco = generate_recommendation(stock_data, predictions_df)
    reco_color = {"Buy": "success", "Sell": "danger", "Hold": "secondary"}

    fig_price = go.Figure(data=[go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Price')])
    if not predictions_df.empty:
        fig_price.add_trace(go.Scatter(x=predictions_df['Date'], y=predictions_df['Predicted_Close'], mode='lines', name='SVR Prediction', line=dict(color='#00BFFF', width=2, dash='dash')))
    fig_price.update_layout(title="Price Chart & AI Forecast", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=stock_data_tech.index, y=stock_data_tech['RSI'], mode='lines', name='RSI'))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig_rsi.update_layout(title="Relative Strength Index (RSI)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D')

    fig_macd = make_subplots(rows=1, cols=1)
    fig_macd.add_trace(go.Scatter(x=stock_data_tech.index, y=stock_data_tech['MACD'], name='MACD'), row=1, col=1)
    fig_macd.add_trace(go.Scatter(x=stock_data_tech.index, y=stock_data_tech['Signal_Line'], name='Signal Line'), row=1, col=1)
    fig_macd.add_trace(go.Bar(x=stock_data_tech.index, y=stock_data_tech['MACD_Hist'], name='Histogram'), row=1, col=1)
    fig_macd.update_layout(title="MACD", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D')
    
    news_content = [dbc.ListGroupItem([html.H6(html.A(a['title'], href=a.get('link'), target='_blank')), html.P(f"Publisher: {a.get('publisher', 'N/A')}", className="small text-muted")]) for a in news if 'link' in a]
    
    actions_content = []
    if dividends is not None and not dividends.empty:
        actions_content.extend([html.H5("Recent Dividends"), dbc.Table.from_dataframe(dividends, dark=True, striped=True, bordered=True)])
    if splits is not None and not splits.empty:
        actions_content.extend([html.H5("Recent Stock Splits"), dbc.Table.from_dataframe(splits, dark=True, striped=True, bordered=True)])
    if not actions_content: actions_content.append(dbc.Alert("No recent corporate actions found.", color="info"))

    content_layout = html.Div([
        html.Div([
            html.H3(stock_info.get('longName', ticker.upper())),
            html.H5(f"{stock_info.get('symbol')} | {stock_info.get('exchangeName')}", style={'color': '#a9a9a9'}),
            dbc.Row([
                dbc.Col(dbc.Button("Buy", id="buy-button", color="success", className="w-100")),
                dbc.Col(dbc.Button("Sell", id="sell-button", color="danger", className="w-100")),
                dbc.Col(dbc.Button("Add to Watchlist", id="watchlist-button", color="info", outline=True, className="w-100")),
                dbc.Col(dbc.Button("Set Price Alert", id="alert-button", color="warning", outline=True, className="w-100")),
            ], className="mt-3", justify="center"),
        ], className="mb-4"),
        dbc.Card(dbc.CardBody([dbc.Row([
            dbc.Col(html.H4("AI Recommendation"), width=12, className="text-center mb-3"),
            dbc.Col(dbc.Button(reco['recommendation'], color=reco_color.get(reco['recommendation']), className="w-100 fw-bold"), md=4),
            dbc.Col(create_metric_card("Risk Level", reco['risk']), md=4),
            dbc.Col(create_metric_card(f"10-Day Target", f"{stock_info.get('currency', '')} {reco['target_price']}"), md=4),
        ])]), className="mb-4"),
        dbc.Tabs([
            dbc.Tab(dcc.Graph(figure=fig_price), label="Price Chart"),
            dbc.Tab(html.Div([dcc.Graph(figure=fig_rsi), dcc.Graph(figure=fig_macd)], className="mt-3"), label="Technical Analysis"),
            dbc.Tab(dbc.ListGroup(news_content, flush=True, className="mt-3"), label="Company News"),
            dbc.Tab(html.Div(actions_content, className="mt-3"), label="Corporate Actions"),
        ])
    ])
    return content_layout, ticker.upper()

@callback(
    [Output("transaction-modal", "is_open"), Output("modal-title", "children"), Output("confirm-transaction-button", "color"), Output("confirm-transaction-button", "custom_data")],
    [Input("buy-button", "n_clicks"), Input("sell-button", "n_clicks")],
    prevent_initial_call=True
)
def open_transaction_modal(buy, sell):
    if ctx.triggered_id == "buy-button": return True, "Buy Stock", "success", "BUY"
    if ctx.triggered_id == "sell-button": return True, "Sell Stock", "danger", "SELL"
    return False, "", "", ""

@callback(
    [Output("wallet-balance-store", "data"), Output("portfolio-store", "data"), Output("trading-history-store", "data"), Output("wallet-history-store", "data"), Output("transaction-alert-placeholder", "children"), Output("transaction-modal", "is_open", allow_duplicate=True)],
    Input("confirm-transaction-button", "n_clicks"),
    [State("confirm-transaction-button", "custom_data"), State("quantity-input", "value"), State("current-ticker-store", "data"), State("wallet-balance-store", "data"), State("portfolio-store", "data"), State("trading-history-store", "data"), State("wallet-history-store", "data")],
    prevent_initial_call=True # THIS LINE IS THE FIX
)
def execute_transaction(n, trans_type, qty, ticker, balance, portfolio, trade_hist, wallet_hist):
    if not all([trans_type, qty, ticker]):
        return (dash.no_update,) * 4 + (dbc.Alert("Invalid details.", color="warning"), False)
    try:
        price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
        value = qty * price
        if trans_type == "BUY":
            if balance < value: return (dash.no_update,) * 4 + (dbc.Alert("Insufficient funds.", color="danger"), False)
            balance -= value
            if ticker in portfolio:
                new_qty = portfolio[ticker]['quantity'] + qty
                new_avg = ((portfolio[ticker]['avg_price'] * portfolio[ticker]['quantity']) + value) / new_qty
                portfolio[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
            else:
                portfolio[ticker] = {'quantity': qty, 'avg_price': price}
            msg, color = f"Successfully purchased {qty} shares of {ticker}.", "success"
        elif trans_type == "SELL":
            if ticker not in portfolio or portfolio[ticker]['quantity'] < qty: return (dash.no_update,) * 4 + (dbc.Alert("Not enough shares to sell.", color="danger"), False)
            profit = (price - portfolio[ticker]['avg_price']) * qty
            balance += value
            if profit > 0:
                fee = profit * 0.10
                balance -= fee
                wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"Brokerage fee on {ticker} profit", 'Amount': f"-₹{fee:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                msg = f"Sold {qty} shares of {ticker} for a profit of ₹{profit:,.2f}. A 10% brokerage fee (₹{fee:,.2f}) was applied."
            else:
                msg = f"Sold {qty} shares of {ticker}."
            portfolio[ticker]['quantity'] -= qty
            if portfolio[ticker]['quantity'] == 0: del portfolio[ticker]
            color = "success"
        trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': trans_type, 'Quantity': qty, 'Price': f"₹{price:,.2f}", 'Total': f"₹{value:,.2f}"})
        wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"{trans_type} {ticker}", 'Amount': f"-₹{value:,.2f}" if trans_type == "BUY" else f"+₹{value,.2f}", 'Balance': f"₹{balance:,.2f}"})
        return balance, portfolio, trade_hist, wallet_hist, dbc.Alert(msg, color=color, duration=5000), False
    except Exception as e:
        return (dash.no_update,) * 4 + (dbc.Alert(f"Transaction failed: {e}", color="danger"), False)

@callback(
    [Output("watchlist-store", "data"), Output("watchlist-alert-placeholder", "children"), Output("watchlist-button", "children"), Output("watchlist-button", "outline")],
    Input("watchlist-button", "n_clicks"),
    [State("current-ticker-store", "data"), State("watchlist-store", "data")],
    prevent_initial_call=True
)
def update_watchlist(n, ticker, watchlist):
    if not ticker: return dash.no_update
    watchlist = watchlist or []
    if ticker in watchlist:
        watchlist.remove(ticker)
        alert, text, out = dbc.Alert(f"{ticker} removed from watchlist.", color="warning", duration=3000), "Add to Watchlist", True
    else:
        watchlist.append(ticker)
        alert, text, out = dbc.Alert(f"{ticker} added to watchlist.", color="success", duration=3000), "On Watchlist", False
    return watchlist, alert, text, out

@callback(
    [Output("alert-modal", "is_open"), Output("upper-alert-input", "value"), Output("lower-alert-input", "value")],
    Input("alert-button", "n_clicks"),
    [State("current-ticker-store", "data"), State("price-alert-store", "data")],
    prevent_initial_call=True,
)
def open_alert_modal(n, ticker, alerts):
    if not ticker: return False, None, None
    a = alerts.get(ticker, {})
    return True, a.get('upper'), a.get('lower')

@callback(
    [Output("price-alert-store", "data"), Output("alert-modal", "is_open", allow_duplicate=True), Output("transaction-alert-placeholder", "children", allow_duplicate=True)],
    Input("confirm-alert-button", "n_clicks"),
    [State("upper-alert-input", "value"), State("lower-alert-input", "value"), State("current-ticker-store", "data"), State("price-alert-store", "data")],
    prevent_initial_call=True
)
def set_price_alert(n, upper, lower, ticker, alerts):
    if not ticker: return dash.no_update
    alerts = alerts or {}
    if upper is None and lower is None:
        if ticker in alerts:
            del alerts[ticker]
            msg = f"Alerts for {ticker} cleared."
        else:
            return dash.no_update, False, dash.no_update
    else:
        alerts[ticker] = {}
        if upper is not None: alerts[ticker]['upper'] = upper
        if lower is not None: alerts[ticker]['lower'] = lower
        msg = f"Price alerts for {ticker} set/updated."
    return alerts, False, dbc.Alert(msg, color="info", duration=4000)
