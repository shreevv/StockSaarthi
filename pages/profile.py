# pages/profile.py

import dash
from dash import html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd

dash.register_page(__name__, name='Profile')

# Get the initial default values from app.py for the reset
from app import initial_wallet_balance, initial_wallet_history

layout = dbc.Container([
    html.H2("My Profile & Settings"),
    html.Hr(),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Account Management", className="card-title"),
                    html.P("This will reset your wallet, portfolio, and all histories to their original state."),
                    dbc.Button("Reset Account", id="reset-account-button", color="danger"),
                ])
            ),
            md=6
        )
    ]),

    # Confirmation Modal for the reset
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirm Account Reset")),
        dbc.ModalBody("Are you sure you want to reset your account? This action cannot be undone."),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-reset-button", color="secondary"),
            dbc.Button("Confirm Reset", id="confirm-reset-button", color="danger"),
        ]),
    ], id="reset-modal", is_open=False),

    # Alert to show after reset is successful
    html.Div(id="reset-alert-placeholder")
], fluid=True, className="mt-4")


# Callback to open the confirmation modal
@callback(
    Output("reset-modal", "is_open"),
    Input("reset-account-button", "n_clicks"),
    State("reset-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_reset_modal(n, is_open):
    if n:
        return not is_open
    return is_open

# Callback to perform the reset and close the modal
@callback(
    [Output("wallet-balance-store", "data", allow_duplicate=True),
    Output("portfolio-store", "data", allow_duplicate=True),
    Output("trading-history-store", "data", allow_duplicate=True),
    Output("wallet-history-store", "data", allow_duplicate=True),
    Output("reset-modal", "is_open", allow_duplicate=True),
    Output("reset-alert-placeholder", "children")],
    Input("confirm-reset-button", "n_clicks"),
    prevent_initial_call=True
)
def reset_account_data(n_clicks):
    # Return the initial default values for all stores
    alert = dbc.Alert("Account has been successfully reset.", color="success", dismissable=True, duration=4000)
    return initial_wallet_balance, {}, [], initial_wallet_history, False, alert

# Callback to just close the modal with the cancel button
@callback(
    Output("reset-modal", "is_open", allow_duplicate=True),
    Input("cancel-reset-button", "n_clicks"),
    State("reset-modal", "is_open"),
    prevent_initial_call=True,
)
def close_reset_modal(n, is_open):
    if n:
        return not is_open
    return is_open
