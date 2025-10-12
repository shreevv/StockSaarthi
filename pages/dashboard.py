# pages/dashboard.py

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from utils.data_handler import fetch_stock_data, get_key_metrics
# --- NEW: Import the SVR model function ---
from utils.ml_model import train_and_predict_svr

dash.register_page(__name__, path='/', name='Dashboard')

# Helper function to create a metric card
def create_metric_card(label, value, class_name=""):
    return html.Div(
        [
            html.P(label, className="metric-card-label"),
            html.H5(value, className=f"metric-card-value {class_name}")
        ],
        className="metric-card"
    )

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("AI Stock Analysis Dashboard"), width=12, className="mb-4 text-center"),
    ], align="center"),
    
    dbc.Row([
        dbc.Col(dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)", type="text"), width=9),
        dbc.Col(dbc.Button("Analyze Stock", id="analyze-button", color="primary", className="w-100"), width=3)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(
            dcc.Loading(
                id="loading-spinner",
                type="default",
                children=html.Div(id="dashboard-content")
            )
        , width=12)
    ])
], fluid=True, className="mt-4")


@callback(
    Output("dashboard-content", "children"),
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value")
)
def update_dashboard(n_clicks, ticker):
    if n_clicks is None or not ticker:
        return html.Div("Please enter a stock ticker and click 'Analyze'.", style={'textAlign': 'center', 'marginTop': '2rem'})

    stock_data, stock_info = fetch_stock_data(ticker.upper())

    if stock_data is None:
        return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'. Please check the ticker and try again.", color="danger")

    # Get Metrics
    metrics, change_color = get_key_metrics(stock_info, stock_data)

    # --- NEW: Train model and get predictions ---
    predictions_df = train_and_predict_svr(stock_data, days_to_predict=10)

    # Create Candlestick Chart
    fig = go.Figure(data=[go.Candlestick(
        x=stock_data.index, open=stock_data['Open'], high=stock_data['High'],
        low=stock_data['Low'], close=stock_data['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name='Price'
    )])

    # --- NEW: Add prediction trace to the chart ---
    if not predictions_df.empty:
        fig.add_trace(go.Scatter(
            x=predictions_df['Date'],
            y=predictions_df['Predicted_Close'],
            mode='lines',
            name='SVR Prediction',
            line=dict(color='#00BFFF', width=2, dash='dash') # Deep Sky Blue, dashed line
        ))
    
    fig.update_layout(
        title=f"{stock_info.get('longName', ticker.upper())} Price Chart & AI Forecast",
        template="plotly_dark", xaxis_rangeslider_visible=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D',
        font=dict(family="Lato, sans-serif", color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # --- NEW: Create a summary for the prediction ---
    prediction_summary_text = "Prediction data not available."
    if not predictions_df.empty:
        next_day_price = predictions_df['Predicted_Close'].iloc[0]
        currency = stock_info.get('currency', 'USD')
        prediction_summary_text = f"The AI model predicts the price to be around {currency} {next_day_price:,.2f} tomorrow."

    # Build the Layout with Metrics, Prediction Summary, and Chart
    content_layout = html.Div([
        # Stock Header
        html.Div([
            html.H3(stock_info.get('longName', ticker.upper())),
            html.H5(f"{stock_info.get('symbol')} | {stock_info.get('exchangeName')}", style={'color': '#a9a9a9'}),
        ], className="mb-4"),
        
        # Row 1 of Metrics
        dbc.Row([
            dbc.Col(create_metric_card("Current Price", metrics["Current Price"]), md=3),
            dbc.Col(create_metric_card("Price Change", metrics["Price Change"], 
                                       class_name="positive-change" if change_color == 'green' else "negative-change"), md=3),
            dbc.Col(create_metric_card("Volume", metrics["Volume"]), md=3),
            dbc.Col(create_metric_card("Avg. Volume", metrics["Avg. Volume"]), md=3),
        ]),
        
        # Row 2 of Metrics
        dbc.Row([
            dbc.Col(create_metric_card("52-Week High", metrics["52-Week High"]), md=3),
            dbc.Col(create_metric_card("52-Week Low", metrics["52-Week Low"]), md=3),
            dbc.Col(create_metric_card("Market Cap", metrics["Market Cap"]), md=3),
            dbc.Col(create_metric_card("P/E Ratio", metrics["P/E Ratio"]), md=3),
        ]),
        
        # --- NEW: AI Prediction Summary Card ---
        dbc.Card(
            dbc.CardBody([
                html.H5("AI Price Forecast", className="card-title"),
                html.P(prediction_summary_text, className="card-text")
            ]),
            className="mt-4 mb-4"
        ),
        
        # Chart
        dbc.Card(dcc.Graph(figure=fig))
    ])

    return content_layout
