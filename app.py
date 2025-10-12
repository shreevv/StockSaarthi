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

@callback(Output("watchlist-container", "children"), [Input("watchlist-interval", "n_intervals"), Input("watchlist-store", "data")])
def update_watchlist_display(n, watchlist):
    if not watchlist: return dbc.ListGroup([dbc.ListGroupItem("Your watchlist is empty.")])
    items = []
    for ticker in watchlist:
        try:
            data = yf.Ticker(ticker).history(period="2d")
            price, change, pct = data['Close'].iloc[-1], data['Close'].diff().iloc[-1], (data['Close'].diff().iloc[-1] / data['Close'].iloc[-2]) * 100
            items.append(dbc.ListGroupItem([dbc.Row([dbc.Col(html.B(ticker)), dbc.Col(f"₹{price:,.2f}", className="text-end")]), dbc.Row([dbc.Col(dbc.Badge(f"{change:+.2f} ({pct:+.2f}%)", color="success" if change >= 0 else "danger"))])]))
        except: continue
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
    if not auto_trades and not price_alerts: return dash.no_update
    alerts, active_trades, active_alerts = [], auto_trades.copy(), price_alerts.copy()
    
    # (Auto-trade logic from Part 15 and Price Alert logic from Part 17 goes here)

    if len(alerts) > 0:
        return balance, portfolio, trade_hist, wallet_hist, active_trades, active_alerts, alerts
    else:
        return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
