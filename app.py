# app.py
import dash
from dash import dcc, html, page_container, callback, Input, Output, State
import dash_bootstrap_components as dbc
import yfinance as yf
import pandas as pd
from app_instance import app, initial_wallet_balance, initial_wallet_history
from header import header
from footer import footer

server = app.server

app.layout = html.Div([
    dcc.Store(id='wallet-balance-store', data=initial_wallet_balance),
    dcc.Store(id='portfolio-store', data={}),
    dcc.Store(id='trading-history-store', data=[]),
    dcc.Store(id='wallet-history-store', data=initial_wallet_history),
    dcc.Store(id='watchlist-store', data=[]),
    dcc.Store(id='autotrade-store', data={}),
    dcc.Store(id='price-alert-store', data={}),
    dcc.Interval(id='watchlist-interval', interval=15*1000, n_intervals=0),
    dcc.Interval(id='autotrade-interval', interval=30*1000, n_intervals=0),
    dcc.Location(id='url'),
    header,
    html.Main(page_container, id="page-content"),
    footer
])

@callback(
    Output("watchlist-container", "children"),
    [Input("watchlist-interval", "n_intervals"), Input("watchlist-store", "data")]
)
def update_watchlist_display(n, watchlist):
    if not watchlist:
        return dbc.ListGroup([dbc.ListGroupItem("Your watchlist is empty.", className="text-muted")], flush=True)

    items = []
    for ticker in watchlist:
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty and len(data) > 1:
                price = data['Close'].iloc[-1]
                change = data['Close'].diff().iloc[-1]
                change_pct = (change / data['Close'].iloc[-2]) * 100
                color = "var(--gain-color)" if change >= 0 else "var(--loss-color)"
                item = dbc.ListGroupItem([
                    dbc.Row([
                        dbc.Col(html.B(ticker), width=6),
                        dbc.Col(f"₹{price:,.2f}", className="text-end", width=6)
                    ]),
                    dbc.Row([
                        dbc.Col(html.Span(f"{change:+.2f} ({change_pct:+.2f}%)", style={'color': color, 'fontSize': '0.9em'}))
                    ])
                ], className="py-2")
                items.append(item)
        except Exception: continue
    return dbc.ListGroup(items, flush=True)

@callback(
    [Output("wallet-balance-store", "data", allow_duplicate=True),
     Output("portfolio-store", "data", allow_duplicate=True),
     Output("trading-history-store", "data", allow_duplicate=True),
     Output("wallet-history-store", "data", allow_duplicate=True),
     Output("autotrade-store", "data", allow_duplicate=True),
     Output("price-alert-store", "data", allow_duplicate=True),
     Output("autotrade-alert-placeholder", "children")],
    Input("autotrade-interval", "n_intervals"),
    [State("autotrade-store", "data"), State("price-alert-store", "data"),
     State("wallet-balance-store", "data"), State("portfolio-store", "data"),
     State("trading-history-store", "data"), State("wallet-history-store", "data")],
    prevent_initial_call=True
)
def background_engine(n, auto_trades, price_alerts, balance, portfolio, trade_hist, wallet_hist):
    if not auto_trades and not price_alerts:
        return dash.no_update

    alerts, active_trades, active_alerts = [], auto_trades.copy(), price_alerts.copy()

    # Auto-Trade Logic
    for ticker, params in auto_trades.items():
        try:
            current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            trade_executed, alert_msg = False, ""
            if params['type'] == 'BUY' and current_price <= params['target']:
                qty, cost = 10, 10 * current_price
                if balance >= cost:
                    balance -= cost
                    if ticker in portfolio:
                        new_qty = portfolio[ticker]['quantity'] + qty
                        new_avg = ((portfolio[ticker]['avg_price'] * portfolio[ticker]['quantity']) + cost) / new_qty
                        portfolio[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
                    else:
                        portfolio[ticker] = {'quantity': qty, 'avg_price': current_price}
                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-BUY', 'Quantity': qty, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{cost:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-BUY {ticker}", 'Amount': f"-₹{cost:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg, trade_executed = f"Auto-Trade: Bought {qty} shares of {ticker}.", True
            elif params['type'] == 'SELL' and current_price >= params['target']:
                if ticker in portfolio and portfolio[ticker]['quantity'] > 0:
                    qty, sale = portfolio[ticker]['quantity'], portfolio[ticker]['quantity'] * current_price
                    balance += sale
                    del portfolio[ticker]
                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-SELL', 'Quantity': qty, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{sale:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-SELL {ticker}", 'Amount': f"+₹{sale:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg, trade_executed = f"Auto-Trade: Sold {qty} shares of {ticker}.", True
            if trade_executed:
                del active_trades[ticker]
                alerts.append(dbc.Alert(alert_msg, color="info", dismissable=True, duration=10000))
        except Exception as e:
            print(f"Auto-trade for {ticker} failed: {e}")
            continue

    # Price Alert Logic
    for ticker, params in price_alerts.items():
        try:
            current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            if params.get('upper') and current_price >= params['upper']:
                alerts.append(dbc.Alert(f"Price Alert: {ticker} crossed upper target of {params['upper']}.", color="warning", duration=15000))
                active_alerts[ticker].pop('upper', None)
            if params.get('lower') and current_price <= params['lower']:
                alerts.append(dbc.Alert(f"Price Alert: {ticker} crossed lower target of {params['lower']}.", color="warning", duration=15000))
                active_alerts[ticker].pop('lower', None)
            if not active_alerts.get(ticker): del active_alerts[ticker]
        except Exception as e:
            print(f"Price alert check for {ticker} failed: {e}")
            continue

    return (balance, portfolio, trade_hist, wallet_hist, active_trades, active_alerts, alerts) if alerts else dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
