# app.py

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, page_container, callback, Input, Output, State
import pandas as pd
import yfinance as yf
from sidebar import sidebar, CONTENT_STYLE

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

initial_wallet_balance = 1000000.00
initial_wallet_history = [{'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': 'Initial Deposit', 'Amount': f"+₹{initial_wallet_balance:,.2f}", 'Balance': f"₹{initial_wallet_balance:,.2f}"}]

footer = html.Div(
    dbc.Card(
        dbc.CardBody([
            html.H6("Demonstration Time Travel"),
            dcc.Slider(id='time-slider', min=0, max=10, step=1, marks={i: f'Day {i}' for i in range(11)}, value=0),
            # --- NEW: Placeholder for auto-trade alerts ---
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
    # --- NEW: Store for active auto-trade jobs ---
    dcc.Store(id='autotrade-store', data={}), # e.g., {'AAPL': {'type': 'BUY', 'target': 150}}

    dcc.Interval(id='watchlist-interval', interval=15*1000, n_intervals=0),
    # --- NEW: Interval for the auto-trade engine ---
    dcc.Interval(id='autotrade-interval', interval=30*1000, n_intervals=0), # Check every 30 seconds

    dcc.Location(id='url'),
    sidebar,
    html.Div(page_container, style={**CONTENT_STYLE, "paddingBottom": "8rem"}),
    footer
])

# The watchlist callback remains unchanged
@callback(
    Output("watchlist-container", "children"),
    [Input("watchlist-interval", "n_intervals"), Input("watchlist-store", "data")]
)
def update_watchlist_display(n, watchlist):
    # (This function is the same as in Part 14)
    if not watchlist: return dbc.ListGroup([dbc.ListGroupItem("Your watchlist is empty.")])
    items = []
    for ticker in watchlist:
        try:
            data = yf.Ticker(ticker).history(period="2d")
            price, change, pct = data['Close'].iloc[-1], data['Close'].diff().iloc[-1], (data['Close'].diff().iloc[-1] / data['Close'].iloc[-2]) * 100
            items.append(dbc.ListGroupItem([dbc.Row([dbc.Col(html.B(ticker)), dbc.Col(f"₹{price:,.2f}", className="text-end")]), dbc.Row([dbc.Col(dbc.Badge(f"{change:+.2f} ({pct:+.2f}%)", color="success" if change >= 0 else "danger"))])]))
        except: continue
    return dbc.ListGroup(items, flush=True)

# --- NEW: The Automated Trading Engine Callback ---
@callback(
    [Output("wallet-balance-store", "data", allow_duplicate=True),
     Output("portfolio-store", "data", allow_duplicate=True),
     Output("trading-history-store", "data", allow_duplicate=True),
     Output("wallet-history-store", "data", allow_duplicate=True),
     Output("autotrade-store", "data", allow_duplicate=True),
     Output("autotrade-alert-placeholder", "children")],
    Input("autotrade-interval", "n_intervals"),
    [State("autotrade-store", "data"), State("wallet-balance-store", "data"),
     State("portfolio-store", "data"), State("trading-history-store", "data"),
     State("wallet-history-store", "data")],
    prevent_initial_call=True
)
def auto_trade_engine(n, auto_trades, balance, portfolio, trade_hist, wallet_hist):
    if not auto_trades:
        return dash.no_update

    alerts = []
    # Create a copy to modify while iterating
    active_trades = auto_trades.copy()

    for ticker, params in auto_trades.items():
        try:
            current_price = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            trade_executed = False
            alert_msg = ""

            # --- BUY Logic ---
            if params['type'] == 'BUY' and current_price <= params['target']:
                qty_to_buy = 10 # Hardcoded quantity for demo
                total_cost = qty_to_buy * current_price
                if balance >= total_cost:
                    balance -= total_cost
                    # (This is the same portfolio update logic as in the manual buy)
                    if ticker in portfolio:
                        new_qty = portfolio[ticker]['quantity'] + qty_to_buy
                        new_avg = ((portfolio[ticker]['avg_price'] * portfolio[ticker]['quantity']) + total_cost) / new_qty
                        portfolio[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
                    else:
                        portfolio[ticker] = {'quantity': qty_to_buy, 'avg_price': current_price}

                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-BUY', 'Quantity': qty_to_buy, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_cost:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-BUY {ticker}", 'Amount': f"-₹{total_cost:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg = f"Auto-Trade Executed: Bought {qty_to_buy} shares of {ticker} at {current_price:,.2f}."
                    trade_executed = True

            # --- SELL Logic ---
            elif params['type'] == 'SELL' and current_price >= params['target']:
                if ticker in portfolio and portfolio[ticker]['quantity'] > 0:
                    qty_to_sell = portfolio[ticker]['quantity'] # Sell all shares for demo
                    total_sale = qty_to_sell * current_price
                    balance += total_sale
                    # (This is a simplified version of the manual sell logic)
                    del portfolio[ticker]

                    trade_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Stock': ticker, 'Type': 'AUTO-SELL', 'Quantity': qty_to_sell, 'Price': f"₹{current_price:,.2f}", 'Total': f"₹{total_sale:,.2f}"})
                    wallet_hist.append({'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': f"AUTO-SELL {ticker}", 'Amount': f"+₹{total_sale:,.2f}", 'Balance': f"₹{balance:,.2f}"})
                    alert_msg = f"Auto-Trade Executed: Sold {qty_to_sell} shares of {ticker} at {current_price:,.2f}."
                    trade_executed = True

            if trade_executed:
                del active_trades[ticker] # Remove completed job
                alerts.append(dbc.Alert(alert_msg, color="info", dismissable=True, duration=10000))

        except Exception as e:
            print(f"Auto-trade for {ticker} failed: {e}")
            continue

    # Return updates only if a trade happened
    if len(alerts) > 0:
        return balance, portfolio, trade_hist, wallet_hist, active_trades, alerts
    else:
        return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
