# sidebar.py

import dash
from dash import html
import dash_bootstrap_components as dbc

# Define the style for the sidebar
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#1a1a2e",
    "color": "#ffffff",
}

# Define the main content style
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Define the sidebar layout
sidebar = html.Div(
    [
        html.Div(
            [
                html.Img(src=dash.get_asset_url('logo.jpg'), style={'width': '50px', 'margin-right': '10px'}),
                html.H2("Stocker AI", style={'display': 'inline-block', 'vertical-align': 'middle'}),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
        
        # Navigation links
        dbc.Nav(
            [
                dbc.NavLink("Dashboard", href="/", active="exact"),
                dbc.NavLink("Portfolio & Wallet", href="/portfolio", active="exact"),
                dbc.NavLink("AI Recommendations", href="/recommendations", active="exact"),
                dbc.NavLink("News & Insights", href="/news", active="exact"),
                dbc.NavLink("Profile", href="/profile", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)