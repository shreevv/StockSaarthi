# header.py

import dash_bootstrap_components as dbc
from dash import html, dcc
from app_instance import app

# This component defines the top navigation bar for the entire application.
# It's fixed to the top, so it remains visible as the user scrolls.
header = html.Header(
    dbc.Navbar(
        dbc.Container(
            [
                # The brand logo and name, linking back to the homepage.
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=app.get_asset_url('logo.jpg'), height="40px")),
                            dbc.Col(dbc.NavbarBrand("Stocker AI", className="ms-2 fw-bold")),
                        ],
                        align="center",
                        className="g-0", # g-0 removes gutters
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                # The navigation links for different pages.
                dbc.Nav(
                    [
                        dbc.NavLink("Dashboard", href="/", active="exact"),
                        dbc.NavLink("Portfolio", href="/portfolio", active="exact"),
                        dbc.NavLink("AI Screener", href="/recommendations", active="exact"),
                        dbc.NavLink("Market News", href="/news", active="exact"),
                        dbc.NavLink("Profile", href="/profile", active="exact"),
                        # A dropdown menu for the watchlist, which is dynamically updated.
                        dbc.DropdownMenu(
                            label="My Watchlist",
                            nav=True,
                            in_navbar=True,
                            align_end=True,
                            children=[
                                dcc.Loading(
                                    type="default",
                                    # The content of the dropdown is loaded by a callback in app.py
                                    children=html.Div(id="watchlist-container", style={"minWidth": "300px", "padding": "0.5rem"})
                                )
                            ]
                        ),
                    ],
                    className="ms-auto",
                    navbar=True
                ),
            ],
            fluid=True
        ),
        color="dark",
        dark=True,
        fixed="top",
        className="py-2 shadow-lg"
    )
)
