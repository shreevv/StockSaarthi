# footer.py
import dash_bootstrap_components as dbc
from dash import html, dcc

footer = html.Footer(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([
                        html.H5("StockSaarthi"),
                        html.P("AI-Powered Stock Analysis & Virtual Trading.", className="text-muted")
                    ], md=4),
                    dbc.Col([
                        html.H6("Quick Links"),
                        html.Ul([
                            html.Li(html.A("Dashboard", href="/", className="text-decoration-none text-muted")),
                            html.Li(html.A("Portfolio", href="/portfolio", className="text-decoration-none text-muted")),
                            html.Li(html.A("AI Screener", href="/recommendations", className="text-decoration-none text-muted")),
                        ], className="list-unstyled")
                    ], md=2),
                    dbc.Col([
                        html.H6("Support"),
                        html.Ul([
                            html.Li(html.A("Contact", href="#", className="text-decoration-none text-muted")),
                            html.Li(html.A("FAQ", href="#", className="text-decoration-none text-muted")),
                        ], className="list-unstyled")
                    ], md=2),
                ],
                className="py-4"
            ),
            html.Div(
                dbc.Card(
                    dbc.CardBody([
                        html.H6("Demonstration Time Travel"),
                        dcc.Slider(id='time-slider', min=0, max=10, step=1, marks={i: f'Day {i}' for i in range(11)}, value=0),
                        html.Div(id="autotrade-alert-placeholder", className="mt-3")
                    ]),
                ), className="mb-4"
            ),
            html.Div(
                html.P("© 2025 StockSaarthi. All rights reserved.", className="text-center text-muted small"),
                className="py-3 border-top"
            )
        ],
        fluid=True,
        className="px-4"
    ),
    className="custom-footer",
)
