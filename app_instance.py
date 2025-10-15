# app_instance.py

import dash
import dash_bootstrap_components as dbc
import pandas as pd

# Define shared variables FIRST. This ensures they are created before any other module
# tries to import them. This is a best practice for managing global state in Dash.
initial_wallet_balance = 1000000.00
initial_wallet_history = [{
    'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    'Description': 'Initial Deposit',
    'Amount': f"₹{initial_wallet_balance:,.2f}",
    'Balance': f"₹{initial_wallet_balance:,.2f}"
}]

# Create the Dash app instance SECOND.
# `use_pages=True` enables the pages routing feature.
# We are using a dark theme and Bootstrap icons for a modern look.
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP]
)
