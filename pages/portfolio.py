# pages/portfolio.py

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import yfinance as yf
from utils.ml_model import get_simulated_price # Import our new function

dash.register_page(__name__, name='Portfolio & Wallet')

layout = dbc.Container([
    dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0),
    html.H2("My Portfolio & Wallet", className="mb-4"),

    dbc.Row([dbc.Col(dbc.Card(dbc.CardBody([html.H5("Current Wallet Balance"), html.H3(id="wallet-balance-display")])), width=12)], className="mb-4"),
    dbc.Row([dbc.Col([html.H4("Current Holdings"), dcc.Loading(children=html.Div(id="portfolio-holdings-table"))], width=12)], className="mb-4"),
    dbc.Row([dbc.Col([html.H4("Histories"), dbc.Tabs([dbc.Tab(label="Trading History", tab_id="trading-history"), dbc.Tab(label="Wallet History", tab_id="wallet-history")], id="history-tabs", active_tab="trading-history"), dcc.Loading(children=html.Div(id="history-content", className="mt-3"))], width=12)])

], fluid=True, className="mt-4")

@callback(
    [Output("wallet-balance-display", "children"),
     Output("portfolio-holdings-table", "children"),
     Output("history-content", "children")],
    [Input("interval-component", "n_intervals"),
     Input("history-tabs", "active_tab"),
     Input("time-slider", "value")], # --- NEW: Listen to the slider
    [State("wallet-balance-store", "data"),
     State("portfolio-store", "data"),
     State("trading-history-store", "data"),
     State("wallet-history-store", "data")]
)
def update_portfolio_page(n_intervals, active_tab, time_delta, balance, portfolio, trading_history, wallet_history):

    wallet_display = f"₹{balance:,.2f}"

    if not portfolio:
        holdings_table = dbc.Alert("You do not own any stocks.", color="info")
    else:
        portfolio_data = []
        for ticker, data in portfolio.items():
            current_price = 0
            avg_price = data['avg_price']
            quantity = data['quantity']

            # --- NEW: Use slider value to determine which price to show ---
            if time_delta == 0:
                # On Day 0, show the live price
                try:
                    stock = yf.Ticker(ticker)
                    current_price = stock.history(period='1d')['Close'].iloc[-1]
                except Exception:
                    current_price = avg_price # Fallback to average price on error
            else:
                # On future days, show the simulated profitable price
                current_price = get_simulated_price(ticker, time_delta, avg_price)

            total_value = current_price * quantity
            profit_loss = (current_price - avg_price) * quantity
            profit_loss_pct = (profit_loss / (avg_price * quantity)) * 100 if avg_price > 0 else 0

            portfolio_data.append({
                "Stock": ticker, "Quantity": quantity, "Avg. Price": f"₹{avg_price:,.2f}",
                "Current Price": f"₹{current_price:,.2f}", "Total Value": f"₹{total_value:,.2f}",
                "P/L": f"₹{profit_loss:,.2f}", "P/L %": f"{profit_loss_pct:.2f}%"
            })

        df = pd.DataFrame(portfolio_data)
        holdings_table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, dark=True)

    # History Tabs Logic (unchanged)
    history_content = ""
    if active_tab == "trading-history":
        df = pd.DataFrame(trading_history).iloc[::-1]
        history_content = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, dark=True) if not df.empty else dbc.Alert("No trading history found.", color="info")
    elif active_tab == "wallet-history":
        df = pd.DataFrame(wallet_history).iloc[::-1]
        history_content = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, dark=True) if not df.empty else dbc.Alert("No wallet history found.", color="info")

    return wallet_display, holdings_table, history_content
