# app.py

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, page_container, callback, Input, Output
import pandas as pd
import yfinance as yf
from sidebar import sidebar, CONTENT_STYLE

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

initial_wallet_balance = 1000000.00
initial_wallet_history = [{'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': 'Initial Deposit', 'Amount': f"+₹{initial_wallet_balance:,.2f}", 'Balance': f"₹{initial_wallet_balance:,.2f}"}]

footer = html.Div(dbc.Card(dbc.CardBody([html.H6("Demonstration Time Travel"), dcc.Slider(id='time-slider', min=0, max=10, step=1, marks={i: f'Day {i}' for i in range(11)}, value=0)]), style={"position": "fixed", "bottom": 0, "left": "16rem", "right": 0, "zIndex": 1000, "backgroundColor": "#1a1a2e"}), id="footer")

app.layout = html.Div([
    # Stores
    dcc.Store(id='wallet-balance-store', data=initial_wallet_balance),
    dcc.Store(id='portfolio-store', data={}),
    dcc.Store(id='trading-history-store', data=[]),
    dcc.Store(id='wallet-history-store', data=initial_wallet_history),
    dcc.Store(id='watchlist-store', data=[]), # Watchlist store was already here

    # NEW: Interval for updating watchlist prices
    dcc.Interval(id='watchlist-interval', interval=15*1000, n_intervals=0),

    # Layout components
    dcc.Location(id='url'),
    sidebar,
    html.Div(page_container, style={**CONTENT_STYLE, "paddingBottom": "8rem"}),
    footer
])


# --- NEW: Callback to update the watchlist in the sidebar ---
@callback(
    Output("watchlist-container", "children"),
    [Input("watchlist-interval", "n_intervals"),
     Input("watchlist-store", "data")]
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

if __name__ == '__main__':
    app.run_server(debug=True)
