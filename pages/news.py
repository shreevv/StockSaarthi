import dash
from dash import html
dash.register_page(__name__, name='News & Insights')
layout = html.Div([
    html.H1("Market News & Insights"),
    html.P("Latest financial news will be displayed here.")
])