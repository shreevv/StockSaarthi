# app.py

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, page_container
import pandas as pd
from sidebar import sidebar, CONTENT_STYLE

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

initial_wallet_balance = 1000000.00
initial_wallet_history = [{'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': 'Initial Deposit', 'Amount': f"+₹{initial_wallet_balance:,.2f}", 'Balance': f"₹{initial_wallet_balance:,.2f}"}]

# --- NEW: Define the footer with the time travel slider ---
footer = html.Div(
    dbc.Card(
        dbc.CardBody([
            html.H6("Demonstration Time Travel", className="card-title text-center"),
            dcc.Slider(
                id='time-slider', min=0, max=10, step=1,
                marks={i: f'Day {i}' for i in range(11)},
                value=0,
            ),
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
    dcc.Store(id='recommendations-store', data=[]),

    dcc.Location(id='url'),
    sidebar,

    # --- UPDATED: Main content now includes a bottom margin for the footer ---
    html.Div(page_container, style={**CONTENT_STYLE, "paddingBottom": "8rem"}),

    # --- NEW: Add the footer to the layout ---
    footer
])

if __name__ == '__main__':
    app.run_server(debug=True)
