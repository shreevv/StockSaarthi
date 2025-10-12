# sidebar.py

# --- FIX 1: Import the shared app instance and dcc ---
from app_instance import app
from dash import html, dcc 
import dash_bootstrap_components as dbc

SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0,
    "width": "16rem", "padding": "2rem 1rem", "background-color": "#1a1a2e",
    "color": "#ffffff", "overflowY": "auto"
}

CONTENT_STYLE = {
    "margin-left": "18rem", "margin-right": "2rem", "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.Div(
            [
                # --- FIX 2: Change dash.get_asset_url to app.get_asset_url ---
                html.Img(src=app.get_asset_url('logo.jpg'), style={'width': '50px', 'margin-right': '10px'}),
                html.H2("Stocker AI", style={'display': 'inline-block', 'vertical-align': 'middle'}),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
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
        html.Hr(),
        html.H5("My Watchlist", className="mt-4"),
        dcc.Loading(
            type="default",
            children=html.Div(id="watchlist-container", className="mt-3")
        )
    ],
    style=SIDEBAR_STYLE,
)
