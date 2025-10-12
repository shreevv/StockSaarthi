# app_instance.py

import dash
import dash_bootstrap_components as dbc
import pandas as pd

# --- FIX: DEFINE VARIABLES FIRST ---
initial_wallet_balance = 1000000.00
initial_wallet_history = [{'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 'Description': 'Initial Deposit', 'Amount': f"₹{initial_wallet_balance:,.2f}", 'Balance': f"₹{initial_wallet_balance:,.2f}"}]

# --- INITIALIZE THE APP AFTER DEFINING VARIABLES ---
# The app initialization will trigger the loading of pages, which now have access to the variables above.
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])
