# pages/recommendations.py

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from utils.data_handler import screen_stocks

dash.register_page(__name__, name='AI Recommendations')

TOP_STOCKS_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'SBIN.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS'
]

layout = html.Main(dbc.Container([
    html.H2("AI Stock Screener", className="mb-4"),
    html.Section(
        dbc.Card(
            dbc.CardBody([
                html.P(
                    "Click the button below to run the AI analysis on a predefined list of top stocks. "
                    "The system will evaluate each stock's trend and future price forecast to identify the best 'Buy' opportunities.",
                    className="card-text"
                ),
                dbc.Button("Find Top Stocks", id="run-screener-button", color="primary", size="lg", className="mt-2")
            ]),
        className="mb-4"),
    ),
    dcc.Loading(
        id="loading-screener",
        type="default",
        children=html.Section(id="recommendations-table-container")
    )

], fluid=True, className="mt-4"))


@callback(
    Output("recommendations-table-container", "children"),
    Input("run-screener-button", "n_clicks"),
    prevent_initial_call=True
)
def run_stock_screener(n_clicks):
    if n_clicks is None:
        return ""

    analysis_results = screen_stocks(TOP_STOCKS_LIST)
    
    if not analysis_results:
        return dbc.Alert("The analysis did not return any results. Please try again later.", color="warning", className="mt-4")
        
    df = pd.DataFrame(analysis_results)
    buy_recommendations = df[df['Recommendation'] == 'Buy']
    
    if buy_recommendations.empty:
        return dbc.Alert("AI analysis complete. No strong 'Buy' signals found at this time.", color="info", className="mt-4")
    
    results_table = dbc.Table.from_dataframe(
        buy_recommendations,
        striped=True,
        bordered=True,
        hover=True,
        dark=True,
        responsive=True
    )
    
    return html.Div([
        html.H4("Top 'Buy' Recommendations", className="mt-4"),
        results_table
    ])
