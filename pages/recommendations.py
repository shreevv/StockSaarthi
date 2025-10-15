# pages/recommendations.py
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from utils.data_handler import screen_stocks

dash.register_page(__name__, name='AI Screener')

# Focused list of top Indian stocks for demonstration
TOP_STOCKS_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'SBIN.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS'
]

layout = dbc.Container(fluid=True, className="mt-4", children=[
    html.H2("AI Stock Screener", className="text-center mb-4"),
    dbc.Card(
        dbc.CardBody([
            html.P(
                "This powerful tool runs our proprietary AI analysis on a predefined list of top NSE stocks. The system evaluates each stock to identify the best 'Buy' opportunities in the current market.",
                className="text-center"
            ),
            dbc.Row(justify="center", children=[
                dbc.Col(md=4, children=
                    dbc.Button("Find Top Stocks", id="run-screener-button", className="w-100 btn-primary", size="lg")
                )
            ])
        ]),
        className="mb-4"
    ),
    dcc.Loading(
        id="loading-screener",
        type="default",
        children=html.Div(id="recommendations-table-container")
    )
])

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
        return dbc.Alert("The analysis did not return any results. This may be due to a network issue. Please try again later.", color="warning", className="mt-4")
        
    df = pd.DataFrame(analysis_results)
    buy_recommendations = df[df['Recommendation'] == 'Buy']
    
    if buy_recommendations.empty:
        return dbc.Alert("AI analysis complete. No strong 'Buy' signals found at this time.", color="info", className="mt-4")
    
    table = dbc.Table.from_dataframe(
        buy_recommendations,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True
    )
    
    return dbc.Card(dbc.CardBody([
        html.H4("Top 'Buy' Recommendations", className="mb-3"),
        table
    ]), className="mt-4")
