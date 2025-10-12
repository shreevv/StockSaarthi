import dash
from dash import html
dash.register_page(__name__, name='Profile')
layout = html.Div([
    html.H1("My Profile"),
    html.P("User profile, settings, and KYC information will be on this page.")
])