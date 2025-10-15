# pages/portfolio.py
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from utils.ml_model import get_simulated_price

dash.register_page(__name__, name='Portfolio & Wallet')

layout = dbc.Container([
    dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0),
    html.H2("My Portfolio & Wallet", className="mb-4"),
    html.Section([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([html.H5("Current Wallet Balance"), html.H3(id="wallet-balance-display")])), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([html.H5("Portfolio Allocation"), dcc.Loading(dcc.Graph(id="portfolio-pie-chart", config={'displayModeBar': False}))])), md=6),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([html.H4("Current Holdings"), dcc.Loading(html.Div(id="portfolio-holdings-table"))], width=12)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H4("Histories"),
                dbc.Tabs([
                    dbc.Tab(label="Trading History", tab_id="trading-history"),
                    dbc.Tab(label="Wallet History", tab_id="wallet-history")
                ], id="history-tabs", active_tab="trading-history"),
                dcc.Loading(html.Div(id="history-content", className="mt-3"))
            ], width=12)
        ])
    ])
], fluid=True, className="mt-4")

@callback(
    [Output("wallet-balance-display", "children"),
     Output("portfolio-holdings-table", "children"),
     Output("history-content", "children"),
     Output("portfolio-pie-chart", "figure")],
    [Input("interval-component", "n_intervals"),
     Input("history-tabs", "active_tab"),
     Input("time-slider", "value")],
    [State("wallet-balance-store", "data"),
     State("portfolio-store", "data"),
     State("trading-history-store", "data"),
     State("wallet-history-store", "data")]
)
def update_portfolio_page(n, active_tab, time_delta, balance, portfolio, trade_hist, wallet_hist):
    wallet_display = f"₹{balance:,.2f}"
    pie_fig = go.Figure(data=[go.Pie(labels=['No Holdings'], values=[1])]).update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False).update_traces(textinfo='none', hoverinfo='none')

    if not portfolio:
        holdings_table = dbc.Alert("You do not own any stocks.", color="info")
    else:
        portfolio_data, pie_labels, pie_values = [], [], []
        for ticker, data in portfolio.items():
            avg_price, quantity = data['avg_price'], data['quantity']
            current_price = get_simulated_price(ticker, time_delta, avg_price) if time_delta > 0 else yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            total_value = current_price * quantity
            profit_loss = (current_price - avg_price) * quantity
            profit_loss_pct = (profit_loss / (avg_price * quantity)) * 100 if avg_price > 0 else 0
            
            portfolio_data.append({"Stock": ticker, "Quantity": quantity, "Avg. Price": f"₹{avg_price:,.2f}", "Current Price": f"₹{current_price:,.2f}", "Total Value": f"₹{total_value:,.2f}", "P/L": f"₹{profit_loss:,.2f}", "P/L %": f"{profit_loss_pct:.2f}%"})
            pie_labels.append(ticker)
            pie_values.append(total_value)

        holdings_table = dbc.Table.from_dataframe(pd.DataFrame(portfolio_data), striped=True, bordered=True, hover=True, dark=True)
        pie_fig = go.Figure(data=[go.Pie(labels=pie_labels, values=pie_values, hole=.3)]).update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=-0.4))

    history_content = ""
    if active_tab == "trading-history":
        df = pd.DataFrame(trade_hist).iloc[::-1]
        history_content = dbc.Table.from_dataframe(df, dark=True) if not df.empty else dbc.Alert("No trading history.", color="info")
    elif active_tab == "wallet-history":
        df = pd.DataFrame(wallet_hist).iloc[::-1]
        history_content = dbc.Table.from_dataframe(df, dark=True) if not df.empty else dbc.Alert("No wallet history.", color="info")
        
    return wallet_display, holdings_table, history_content, pie_fig
