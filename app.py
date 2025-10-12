# app.py

import dash
from app_instance import app, initial_wallet_balance, initial_wallet_history
import dash_bootstrap_components as dbc
from dash import dcc, html, page_container, callback, Input, Output, State
import pandas as pd
import yfinance as yf
from sidebar import sidebar, CONTENT_STYLE

# This line is critical for deployment
server = app.server

footer = html.Div(
    dbc.Card(
        dbc.CardBody([
            html.H6("Demonstration Time Travel"),
            dcc.Slider(id='time-slider', min=0, max=10, step=1, marks={i: f'Day {i}' for i in range(11)}, value=0),
            html.Div(id="autotrade-alert-placeholder", className="mt-2")
        ]),
        style={"position": "fixed", "bottom": 0, "left": "16rem", "right": 0, "zIndex": 1000, "backgroundColor": "#1a1a2e"}
    ),
    id="footer"
)

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
    sidebar,
    html.Div(page_container, style={**CONTENT_STYLE, "paddingBottom": "8rem"}),
    footer
])

@callback(
    Output("watchlist-container", "children"),
    [Input("watchlist-interval", "n_intervals"), Input("watchlist-store", "data")]
)
def update_watchlist_display(n, watchlist):
    if not watchlist:
        return dbc.ListGroup([dbc.ListGroupItem("Your watchlist is empty.")])
    
    watchlist_items = []
    for ticker in watchlist:
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty:
                price = data['Close'].iloc[-1]
                change = data['Close'].diff().iloc[-1]
                change_pct = (change / data['Close'].iloc[-2]) * 100
                color = "success" if change >= 0 else "danger"

                item = dbc.ListGroupItem([
                    dbc.Row([
                        dbc.Col(html.B(ticker), width="auto"),
                        dbc.Col(f"₹{price:,.2f}", className="text-end")
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Badge(f"{change:+.2f} ({change_pct:+.2f}%)", color=color), width="auto")
                    ])
                ], style={"backgroundColor": "#2a2a3e", "border": "none", "marginBottom": "5px"})
                watchlist_items.append(item)
        except Exception:
            continue
            
    return dbc.ListGroup(watchlist_items, flush=True)

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

    alerts = []
    active_trades = auto_trades.copy()
    active_alerts = price_alerts.copy()

    # Auto-Trade Logic
    for ticker, params in auto_trades.items():
        try:
            current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            trade_executed, alert_msg = False, ""

            if params['type'] == 'BUY' and current_price <= params['target']:
                qty_to_buy, total_cost = 10, 10 * current_price
                if balance >= total_cost:
                    balance -= total_cost
                    if ticker in portfolio:
                        new_qty = portfolio[ticker]['quantity'] + qty_to_buy
                        new_avg = ((portfolio[ticker]['avg_price'] * portfolio[ticker]['quantity']) + total_cost) / new_qty
                        portfolio[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
                    else:
                        portfolio[ticker] = {'quantity': qty_to_buy, 'avg_price': current_price}
                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-BUY', 'Quantity': qty_to_buy, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_cost:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-BUY {ticker}", 'Amount': f"-₹{total_cost:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg, trade_executed = f"Auto-Trade Executed: Bought {qty_to_buy} shares of {ticker}.", True
            
            elif params['type'] == 'SELL' and current_price >= params['target']:
                if ticker in portfolio and portfolio[ticker]['quantity'] > 0:
                    qty_to_sell, total_sale = portfolio[ticker]['quantity'], portfolio[ticker]['quantity'] * current_price
                    balance += total_sale
                    del portfolio[ticker]
                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-SELL', 'Quantity': qty_to_sell, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_sale:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-SELL {ticker}", 'Amount': f"+₹{total_sale:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg, trade_executed = f"Auto-Trade Executed: Sold {qty_to_sell} shares of {ticker}.", True

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
                alerts.append(dbc.Alert(f"Price Alert: {ticker} has crossed upper target of {params['upper']}.", color="warning", duration=15000))
                active_alerts[ticker].pop('upper', None)
            if params.get('lower') and current_price <= params['lower']:
                alerts.append(dbc.Alert(f"Price Alert: {ticker} has crossed lower target of {params['lower']}.", color="warning", duration=15000))
                active_alerts[ticker].pop('lower', None)
            if not active_alerts.get(ticker):
                del active_alerts[ticker]
        except Exception as e:
            print(f"Price alert check for {ticker} failed: {e}")
            continue
    
    if len(alerts) > 0:
        return balance, portfolio, trade_hist, wallet_hist, active_trades, active_alerts, alerts
    else:
        return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
