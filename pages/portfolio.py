# pages/portfolio.py
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from utils.ml_model import get_simulated_price

dash.register_page(__name__, name='Portfolio & Wallet')

layout = dbc.Container(fluid=True, className="mt-4", children=[
    dcc.Interval(id='interval-component', interval=15*1000),
    html.Div(id="add-funds-alert-placeholder"),
    
    dbc.Row([
        dbc.Col(html.H2("My Portfolio & Wallet"), md=9),
        dbc.Col(dbc.Button("Add Funds", id="add-funds-button", className="w-100 btn-primary"), md=3, className="d-flex align-items-center"),
    ]),
    
    html.Hr(),
    
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H5("Current Wallet Balance", className="text-muted"), html.H3(id="wallet-balance-display", className="fw-bold")])), md=6, className="mb-3"),
        dbc.Col(dbc.Card(dbc.CardBody([html.H5("Portfolio Allocation", className="text-muted"), dcc.Loading(dcc.Graph(id="portfolio-pie-chart", config={'displayModeBar': False}))])), md=6, className="mb-3"),
    ]),
    
    dbc.Card(dbc.CardBody([
        html.H4("Current Holdings"),
        dcc.Loading(html.Div(id="portfolio-holdings-table"))
    ]), className="mb-4"),

    dbc.Card(dbc.CardBody([
        html.H4("Histories"),
        dbc.Tabs([
            dbc.Tab(label="Trading History", tab_id="trading-history"),
            dbc.Tab(label="Wallet History", tab_id="wallet-history")
        ], id="history-tabs", active_tab="trading-history"),
        dcc.Loading(html.Div(id="history-content", className="mt-3"))
    ])),

    # Modal to Add Funds
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Add Virtual Funds")),
        dbc.ModalBody([
            html.P("Select an amount to add to your virtual wallet."),
            dbc.InputGroup([
                dbc.InputGroupText("₹"),
                dbc.Input(id="add-funds-input", type="number", min=1000, step=1000, placeholder="e.g., 50000"),
            ])
        ]),
        dbc.ModalFooter(dbc.Button("Confirm Deposit", id="confirm-add-funds-button", className="btn-primary")),
    ], id="add-funds-modal", is_open=False),
])

# Callback to open/close the modal
@callback(
    Output("add-funds-modal", "is_open"),
    [Input("add-funds-button", "n_clicks"), Input("confirm-add-funds-button", "n_clicks")],
    State("add-funds-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_add_funds_modal(n_open, n_confirm, is_open):
    if n_open or n_confirm:
        return not is_open
    return is_open

# Callback to handle adding funds
@callback(
    [Output("wallet-balance-store", "data", allow_duplicate=True),
     Output("wallet-history-store", "data", allow_duplicate=True),
     Output("add-funds-alert-placeholder", "children")],
    Input("confirm-add-funds-button", "n_clicks"),
    [State("add-funds-input", "value"),
     State("wallet-balance-store", "data"),
     State("wallet-history-store", "data")],
    prevent_initial_call=True,
)
def add_funds_to_wallet(n, amount, balance, history):
    if not amount or amount <= 0:
        return dash.no_update, dash.no_update, dbc.Alert("Please enter a valid amount.", color="danger")
    
    new_balance = balance + amount
    history.append({
        'Date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Description': 'Virtual Deposit',
        'Amount': f"+₹{amount:,.2f}",
        'Balance': f"₹{new_balance:,.2f}"
    })
    
    alert = dbc.Alert(f"Successfully added ₹{amount:,.2f} to your wallet.", color="success", duration=4000)
    return new_balance, history, alert

# Main callback to update portfolio page
# ... (this callback remains the same but will now use the light theme for tables and charts) ...
