# pages/profile.py

import dash
from dash import html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

dash.register_page(__name__, name='Profile')

from app import initial_wallet_balance, initial_wallet_history

layout = dbc.Container([
    html.H2("My Profile & Settings"),
    html.Hr(),
    dbc.Row([
        # --- NEW: User Details Card ---
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("User Details", className="card-title"),
                    html.P("Username: demo_user"),
                    html.P("Email: user@example.com"),
                    html.P("Joined: 2025-10-13"),
                ])
            ), md=6, className="mb-4"
        ),
        # --- NEW: KYC Status Card ---
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("KYC Status", className="card-title"),
                    html.Div([
                        html.Span("Verified", className="me-2"),
                        # Using a Bootstrap icon class
                        html.I(className="bi bi-patch-check-fill text-success")
                    ], className="d-flex align-items-center"),
                    dbc.Button("View Details", color="secondary", outline=True, size="sm", className="mt-3"),
                ])
            ), md=6, className="mb-4"
        ),
        # --- NEW: Nominee Declaration Card ---
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Nominee Declaration", className="card-title"),
                    html.P("You have 1 nominee added to your account."),
                    dbc.Button("Manage Nominees", color="secondary", outline=True, size="sm", className="mt-2"),
                ])
            ), md=6, className="mb-4"
        ),
        # Account Management Card (from Part 10)
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Account Management", className="card-title"),
                    html.P("This will reset your wallet, portfolio, and all histories to their original state."),
                    dbc.Button("Reset Account", id="reset-account-button", color="danger"),
                ])
            ), md=6, className="mb-4"
        ),
    ]),

    # Confirmation Modal for the reset (from Part 10)
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirm Account Reset")),
        dbc.ModalBody("Are you sure? This action cannot be undone."),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-reset-button", color="secondary"),
            dbc.Button("Confirm Reset", id="confirm-reset-button", color="danger"),
        ]),
    ], id="reset-modal", is_open=False),

    html.Div(id="reset-alert-placeholder")
], fluid=True, className="mt-4")

# --- The reset callbacks are unchanged from Part 10 ---
# ... (toggle_reset_modal callback) ...
# ... (reset_account_data callback) ...
# ... (close_reset_modal callback) ...
