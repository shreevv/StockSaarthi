# app.py

import dash
from dash import dcc, html, page_container, callback, Input, Output, State
import dash_bootstrap_components as dbc
import yfinance as yf
import pandas as pd

from app_instance import app, initial_wallet_balance, initial_wallet_history
from header import header
from footer import footer

# This line is critical for deployment on services like Heroku
server = app.server

# The main application layout is now cleaner, using the imported header and footer.
app.layout = html.Div([
    # Dash components for storing data in the user's browser session
    dcc.Store(id='wallet-balance-store', data=initial_wallet_balance),
    dcc.Store(id='portfolio-store', data={}),
    dcc.Store(id='trading-history-store', data=[]),
    dcc.Store(id='wallet-history-store', data=initial_wallet_history),
    dcc.Store(id='watchlist-store', data=[]),
    dcc.Store(id='autotrade-store', data={}),
    dcc.Store(id='price-alert-store', data={}),

    # Interval components to trigger callbacks for real-time updates
    dcc.Interval(id='watchlist-interval', interval=15*1000, n_intervals=0), # 15 seconds
    dcc.Interval(id='autotrade-interval', interval=30*1000, n_intervals=0), # 30 seconds

    dcc.Location(id='url'),

    # The new application structure
    header,
    # The `page_container` is where Dash will render the content of your different pages
    html.Main(page_container, id="page-content"),
    footer
])


@callback(
    Output("watchlist-container", "children"),
    [Input("watchlist-interval", "n_intervals"), Input("watchlist-store", "data")]
)
def update_watchlist_display(n, watchlist):
    """
    Periodically fetches and displays real-time data for stocks in the user's watchlist.
    This callback is located in app.py because its output target is in the header.
    """
    if not watchlist:
        return dbc.ListGroup([dbc.ListGroupItem("Your watchlist is empty.", className="text-white-50")], flush=True)

    watchlist_items = []
    for ticker in watchlist:
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty and len(data) > 1:
                price = data['Close'].iloc[-1]
                change = data['Close'].diff().iloc[-1]
                change_pct = (change / data['Close'].iloc[-2]) * 100
                color = "success" if change >= 0 else "danger"

                item = dbc.ListGroupItem(
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.B(ticker), width="auto"),
                                dbc.Col(f"₹{price:,.2f}", className="text-end"),
                            ],
                            justify="between",
                            align="center"
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Badge(f"{change:+.2f} ({change_pct:+.2f}%)", color=color)),
                            ]
                        )
                    ],
                    className="bg-dark text-light"
                )
                watchlist_items.append(item)
        except Exception as e:
            print(f"Error fetching watchlist data for {ticker}: {e}")
            continue

    return dbc.ListGroup(watchlist_items, flush=True)


@callback(
    [
        Output("wallet-balance-store", "data", allow_duplicate=True),
        Output("portfolio-store", "data", allow_duplicate=True),
        Output("trading-history-store", "data", allow_duplicate=True),
        Output("wallet-history-store", "data", allow_duplicate=True),
        Output("autotrade-store", "data", allow_duplicate=True),
        Output("price-alert-store", "data", allow_duplicate=True),
        Output("autotrade-alert-placeholder", "children")
    ],
    Input("autotrade-interval", "n_intervals"),
    [
        State("autotrade-store", "data"),
        State("price-alert-store", "data"),
        State("wallet-balance-store", "data"),
        State("portfolio-store", "data"),
        State("trading-history-store", "data"),
        State("wallet-history-store", "data")
    ],
    prevent_initial_call=True
)
def background_engine(n, auto_trades, price_alerts, balance, portfolio, trade_hist, wallet_hist):
    """
    A background engine that runs periodically to check for auto-trade triggers and price alerts.
    This powerful feature allows the app to perform actions even when the user is idle.
    """
    if not auto_trades and not price_alerts:
        return dash.no_update

    alerts = []
    active_trades = auto_trades.copy()
    active_alerts = price_alerts.copy()

    # --- Auto-Trade Logic ---
    for ticker, params in auto_trades.items():
        try:
            current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            trade_executed = False
            alert_msg = ""

            # BUY condition
            if params['type'] == 'BUY' and current_price <= params['target']:
                qty_to_buy, total_cost = 10, 10 * current_price
                if balance >= total_cost:
                    balance -= total_cost
                    # Update portfolio logic
                    if ticker in portfolio:
                        new_qty = portfolio[ticker]['quantity'] + qty_to_buy
                        new_avg = ((portfolio[ticker]['avg_price'] * portfolio[ticker]['quantity']) + total_cost) / new_qty
                        portfolio[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
                    else:
                        portfolio[ticker] = {'quantity': qty_to_buy, 'avg_price': current_price}

                    # Update histories
                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-BUY', 'Quantity': qty_to_buy, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_cost:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-BUY {ticker}", 'Amount': f"-₹{total_cost:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg, trade_executed = f"Auto-Trade Executed: Bought {qty_to_buy} shares of {ticker}.", True

            # SELL condition
            elif params['type'] == 'SELL' and current_price >= params['target']:
                if ticker in portfolio and portfolio[ticker]['quantity'] > 0:
                    qty_to_sell = portfolio[ticker]['quantity']
                    total_sale = qty_to_sell * current_price
                    balance += total_sale
                    del portfolio[ticker]

                    # Update histories
                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-SELL', 'Quantity': qty_to_sell, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_sale:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-SELL {ticker}", 'Amount': f"+₹{total_sale:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg, trade_executed = f"Auto-Trade Executed: Sold all {qty_to_sell} shares of {ticker}.", True

            if trade_executed:
                del active_trades[ticker]
                alerts.append(dbc.Alert(alert_msg, color="info", dismissable=True, duration=15000))
        except Exception as e:
            print(f"Auto-trade logic failed for {ticker}: {e}")
            continue

    # --- Price Alert Logic ---
    for ticker, params in price_alerts.items():
        try:
            current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            if params.get('upper') and current_price >= params['upper']:
                alerts.append(dbc.Alert(f"Price Alert: {ticker} crossed its upper target of ₹{params['upper']}.", color="warning", duration=15000))
                active_alerts[ticker].pop('upper', None)
            if params.get('lower') and current_price <= params['lower']:
                alerts.append(dbc.Alert(f"Price Alert: {ticker} crossed its lower target of ₹{params['lower']}.", color="warning", duration=15000))
                active_alerts[ticker].pop('lower', None)
            
            # If both upper and lower alerts are gone, remove the ticker
            if not active_alerts.get(ticker):
                del active_alerts[ticker]
        except Exception as e:
            print(f"Price alert check failed for {ticker}: {e}")
            continue

    if alerts:
        return balance, portfolio, trade_hist, wallet_hist, active_trades, active_alerts, alerts
    
    # If no alerts were generated, don't update the outputs
    return dash.no_update


if __name__ == '__main__':
    app.run_server(debug=True)
