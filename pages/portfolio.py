# pages/portfolio.py
import dash
from dash import html
dash.register_page(__name__, name='Portfolio & Wallet')
layout = html.Div([
    html.H1("My Portfolio & Wallet"),
    html.P("This is where your holdings, wallet balance, and transaction history will appear.")
])