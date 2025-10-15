# pages/profile.py
import dash
from dash import html, callback, Input, Output, State
import dash_bootstrap_components as dbc
from app_instance import initial_wallet_balance, initial_wallet_history

dash.register_page(__name__, name='Profile')

layout = dbc.Container(fluid=True, className="mt-4", children=[
    html.H2("My Profile & Settings", className="mb-4"),
    html.Hr(),
    dbc.Row([
        dbc.Col(md=6, children=dbc.Card(dbc.CardBody([
            html.H4("User Details"),
            html.P("Username: demo_user"),
            html.P("Email: user@example.com")
        ]), className="mb-4")),
        dbc.Col(md=6, children=dbc.Card(dbc.CardBody([
            html.H4("KYC Status"),
            html.Div([html.I(className="bi bi-patch-check-fill text-success me-2"), html.Span("Verified")]),
        ]), className="mb-4")),
        dbc.Col(md=6, children=dbc.Card(dbc.CardBody([
            html.H4("Account Management"),
            html.P("Reset your wallet, portfolio, and all histories to the initial state."),
            dbc.Button("Reset Account", id="reset-account-button", color="danger")
        ]), className="mb-4")),
    ]),
    
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirm Account Reset")),
        dbc.ModalBody("Are you sure? This action is irreversible and will delete all your trading data."),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-reset-button", className="btn-secondary"),
            dbc.Button("Confirm Reset", id="confirm-reset-button", color="danger")
        ]),
    ], id="reset-modal", is_open=False),
    
    html.Div(id="reset-alert-placeholder")
])

@callback(
    Output("reset-modal", "is_open"),
    [Input("reset-account-button", "n_clicks"), Input("cancel-reset-button", "n_clicks")],
    State("reset-modal", "is_open"),
    prevent_initial_call=True)
def toggle_reset_modal(n_reset, n_cancel, is_open):
    if n_reset or n_cancel:
        return not is_open
    return is_open

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
    alert = dbc.Alert("Account has been successfully reset.", color="success", dismissable=True, duration=4000)
    return initial_wallet_balance, {}, [], initial_wallet_history, False, alert
