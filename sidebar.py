from app_instance import app # Import the app instance
from dash import html, dcc
import dash_bootstrap_components as dbc

# ... (the rest of your sidebar.py file remains the same)
# The line below will now work correctly
html.Img(src=app.get_asset_url('logo.jpg'), style={'width': '50px', 'margin-right': '10px'}),
# ...

SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0,
    "width": "16rem", "padding": "2rem 1rem", "background-color": "#1a1a2e",
    "color": "#ffffff", "overflowY": "auto" # Added for scrolling if watchlist gets long
}

CONTENT_STYLE = {
    "margin-left": "18rem", "margin-right": "2rem", "padding": "2rem 1rem",
}

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
        # --- NEW: Watchlist Section ---
        html.H5("My Watchlist", className="mt-4"),
        dcc.Loading(
            type="default",
            children=html.Div(id="watchlist-container", className="mt-3")
        )
    ],
    style=SIDEBAR_STYLE,
)
