# app.py

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, page_container
import pandas as pd

# Import the sidebar and its style
from sidebar import sidebar, CONTENT_STYLE

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# --- Initial Data Setup ---
initial_wallet_balance = 1000000.00
initial_wallet_history = [{
    'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    'Description': 'Initial Deposit',
    'Amount': f"+₹{initial_wallet_balance:,.2f}",
    'Balance': f"₹{initial_wallet_balance:,.2f}"
}]

# --- Main App Layout ---
app.layout = html.Div([
    dcc.Store(id='wallet-balance-store', data=initial_wallet_balance),
    dcc.Store(id='portfolio-store', data={}),
    dcc.Store(id='trading-history-store', data=[]),
    dcc.Store(id='wallet-history-store', data=initial_wallet_history),
    dcc.Store(id='watchlist-store', data=[]),
    dcc.Store(id='recommendations-store', data=[]),
    dcc.Store(id='time-slider-store', data=0),

    dcc.Location(id='url'),

    # Integrate the sidebar
    sidebar,
    
    # The page_container will render the content of each page
    html.Div(page_container, style=CONTENT_STYLE)
])

if __name__ == '__main__':
    app.run_server(debug=True)