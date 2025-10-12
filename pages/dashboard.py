# pages/dashboard.py

import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
# --- NEW: Import the new functions ---
from utils.data_handler import fetch_stock_data, get_key_metrics, calculate_technical_indicators, fetch_news
from utils.ml_model import train_and_predict_svr, generate_recommendation
import pandas as pd

dash.register_page(__name__, path='/', name='Dashboard')

# This helper function is unchanged
def create_metric_card(label, value, class_name=""):
    return html.Div([html.P(label, className="metric-card-label"), html.H5(value, className=f"metric-card-value {class_name}")], className="metric-card")

# The main layout structure is unchanged
layout = dbc.Container([
    dcc.Store(id='current-ticker-store', data=None),
    html.H2("AI Stock Analysis Dashboard", className="mb-4 text-center"),
    dbc.Row([
        dbc.Col(dbc.Input(id="stock-ticker-input", placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)", type="text"), width=9),
        dbc.Col(dbc.Button("Analyze Stock", id="analyze-button", color="primary", className="w-100"), width=3)
    ], className="mb-4"),
    html.Div(id="transaction-alert-placeholder"),
    dbc.Row([dbc.Col(dcc.Loading(id="loading-spinner", type="default", children=html.Div(id="dashboard-content")), width=12)]),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody([dbc.Row([dbc.Col(html.P("Quantity:"), width=4), dbc.Col(dbc.Input(id="quantity-input", type="number", min=1, step=1), width=8)])]),
        dbc.ModalFooter(dbc.Button("Confirm", id="confirm-transaction-button")),
    ], id="transaction-modal", is_open=False)
], fluid=True, className="mt-4")


# --- UPDATED: The main callback now builds the tabbed interface ---
@callback(
    Output("dashboard-content", "children"),
    Output("current-ticker-store", "data"),
    Input("analyze-button", "n_clicks"),
    State("stock-ticker-input", "value"),
    prevent_initial_call=True
)
def update_dashboard(n_clicks, ticker):
    if not ticker:
        return html.Div("Please enter a stock ticker."), dash.no_update

    # --- 1. Fetch all data ---
    stock_data, stock_info = fetch_stock_data(ticker.upper())
    if stock_data is None:
        return dbc.Alert(f"Could not retrieve data for '{ticker.upper()}'.", color="danger"), dash.no_update

    stock_data = calculate_technical_indicators(stock_data)
    news_articles = fetch_news(ticker.upper())
    metrics, change_color = get_key_metrics(stock_info, stock_data)
    predictions_df = train_and_predict_svr(stock_data, days_to_predict=10)
    reco = generate_recommendation(stock_data, predictions_df)
    reco_color = {"Buy": "success", "Sell": "danger", "Hold": "secondary"}

    # --- 2. Build Figures and Content for Tabs ---
    # Price Chart (existing logic)
    fig_price = go.Figure(data=[go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Price')])
    if not predictions_df.empty:
        fig_price.add_trace(go.Scatter(x=predictions_df['Date'], y=predictions_df['Predicted_Close'], mode='lines', name='SVR Prediction', line=dict(color='#00BFFF', width=2, dash='dash')))
    fig_price.update_layout(title="Price Chart & AI Forecast", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D')

    # RSI Chart
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], mode='lines', name='RSI'))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought", annotation_position="bottom right")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold", annotation_position="bottom right")
    fig_rsi.update_layout(title="Relative Strength Index (RSI)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D')

    # MACD Chart
    fig_macd = make_subplots(rows=1, cols=1)
    fig_macd.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MACD'], name='MACD'), row=1, col=1)
    fig_macd.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Signal_Line'], name='Signal Line'), row=1, col=1)
    fig_macd.add_trace(go.Bar(x=stock_data.index, y=stock_data['MACD_Hist'], name='Histogram'), row=1, col=1)
    fig_macd.update_layout(title="MACD", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1E1E2D')

    # News Content
    news_content = [
        dbc.ListGroupItem([
            html.H6(html.A(article['title'], href=article.get('link'), target='_blank', className="stretched-link")),
            html.P(f"Publisher: {article.get('publisher', 'N/A')}", className="mb-1 small text-muted")
        ]) for article in news_articles if 'link' in article
    ]

    # --- 3. Assemble the Final Layout ---
    content_layout = html.Div([
        # Header, Recommendation, and Metrics (unchanged)
        html.Div([
            html.H3(stock_info.get('longName', ticker.upper())),
            html.H5(f"{stock_info.get('symbol')} | {stock_info.get('exchangeName')}", style={'color': '#a9a9a9'}),
            dbc.Row([dbc.Col(dbc.Button("Buy", id="buy-button", color="success", className="w-100"), width=6), dbc.Col(dbc.Button("Sell", id="sell-button", color="danger", className="w-100"), width=6)], className="mt-3")
        ], className="mb-4"),
        dbc.Card(dbc.CardBody([dbc.Row([
            dbc.Col(html.H4("AI Recommendation"), width=12, className="text-center"),
            dbc.Col(dbc.Button(reco['recommendation'], color=reco_color.get(reco['recommendation']), className="w-100 fw-bold"), width=4),
            dbc.Col(create_metric_card("Risk Level", reco['risk']), width=4),
            dbc.Col(create_metric_card(f"10-Day Target", f"{stock_info.get('currency', '')} {reco['target_price']}"), width=4)
        ])]), className="mb-4"),

        # --- NEW: Tabbed Interface ---
        dbc.Tabs([
            dbc.Tab(dcc.Graph(figure=fig_price), label="Price Chart"),
            dbc.Tab(
                html.Div([
                    dcc.Graph(figure=fig_rsi),
                    dcc.Graph(figure=fig_macd)
                ], className="mt-3"),
                label="Technical Analysis"
            ),
            dbc.Tab(dbc.ListGroup(news_content, flush=True, className="mt-3"), label="Company News"),
        ])
    ])
    return content_layout, ticker.upper()

# The two transaction callbacks below remain the same as Part 11.
# [Callback to open transaction modal] & [Callback to execute transaction]
# ... (code for these two callbacks is identical to the previous part, not shown here for brevity)
# --- NOTE: For your actual file, you must include the full code for the two transaction callbacks from Part 11 here. ---
