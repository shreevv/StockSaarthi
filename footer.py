# footer.py

import dash_bootstrap_components as dbc
from dash import html, dcc

# The footer provides supplementary information and the time-travel feature.
# It is designed to be informative and consistent with the new layout.
footer = html.Footer(
    dbc.Container(
        [
            html.Hr(),
            # The top section of the footer contains informational links.
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Stocker AI"),
                            html.P("Seamless learning for a better future.", className="text-white-50")
                        ],
                        md=4,
                        className="mb-3"
                    ),
                    dbc.Col(
                        [
                            html.H6("Products"),
                            html.Ul(
                                [
                                    html.Li(html.A("Overview", href="#", className="text-decoration-none text-white-50")),
                                    html.Li(html.A("Solutions", href="#", className="text-decoration-none text-white-50")),
                                    html.Li(html.A("Pricing", href="#", className="text-decoration-none text-white-50")),
                                ],
                                className="list-unstyled"
                            )
                        ],
                        md=2,
                        className="mb-3"
                    ),
                    dbc.Col(
                        [
                            html.H6("Company"),
                            html.Ul(
                                [
                                    html.Li(html.A("About", href="#", className="text-decoration-none text-white-50")),
                                    html.Li(html.A("Jobs", href="#", className="text-decoration-none text-white-50")),
                                    html.Li(html.A("Blog", href="#", className="text-decoration-none text-white-50")),
                                ],
                                className="list-unstyled"
                            )
                        ],
                        md=2,
                        className="mb-3"
                    ),
                    dbc.Col(
                        [
                            html.H6("Support"),
                            html.Ul(
                                [
                                    html.Li(html.A("Contact", href="#", className="text-decoration-none text-white-50")),
                                    html.Li(html.A("Documentation", href="#", className="text-decoration-none text-white-50")),
                                    html.Li(html.A("FAQ", href="#", className="text-decoration-none text-white-50")),
                                ],
                                className="list-unstyled"
                            )
                        ],
                        md=2,
                        className="mb-3"
                    ),
                ],
                justify="between"
            ),
            html.Hr(),
            # The bottom section contains the "Time Travel" feature for simulation.
            dbc.Card(
                dbc.CardBody([
                    html.H6("Demonstration Time Travel"),
                    dcc.Slider(id='time-slider', min=0, max=10, step=1, marks={i: f'Day {i}' for i in range(11)}, value=0),
                    html.Div(id="autotrade-alert-placeholder", className="mt-3")
                ]),
                className="bg-dark"
            ),
            # Copyright notice.
            html.P("© 2025 Stocker AI. All rights reserved.", className="text-center text-white-50 mt-4")
        ],
        fluid=True
    ),
    className="mt-5 p-4",
    style={"backgroundColor": "#1E1E2D"}
)
