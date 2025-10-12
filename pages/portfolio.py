# pages/portfolio.py

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import yfinance as yf

dash.register_page(__name__, name='Portfolio & Wallet')

layout = dbc.Container([
    # --- Auto-refreshing component ---
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # in milliseconds (e.g., 10 seconds)
        n_intervals=0
    ),
    
    html.H2("My Portfolio & Wallet", className="mb-4"),
    
    # --- Row for Wallet Summary ---
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Current Wallet Balance", className="card-title"),
                    html.H3(id="wallet-balance-display", className="card-text")
                ])
            ),
            width=12
        )
    ], className="mb-4"),
    
    # --- Row for Portfolio Holdings ---
    dbc.Row([
        dbc.Col([
            html.H4("Current Holdings"),
            dcc.Loading(children=html.Div(id="portfolio-holdings-table"))
        ], width=12)
    ], className="mb-4"),
    
    # --- Row for Transaction Histories ---
    dbc.Row([
        dbc.Col([
            html.H4("Histories"),
            dbc.Tabs([
                dbc.Tab(label="Trading History", tab_id="trading-history"),
                dbc.Tab(label="Wallet History", tab_id="wallet-history"),
            ], id="history-tabs", active_tab="trading-history"),
            dcc.Loading(children=html.Div(id="history-content", className="mt-3"))
        ], width=12)
    ])
    
], fluid=True, className="mt-4")


# --- Callback to update the entire portfolio page ---
@callback(
    [Output("wallet-balance-display", "children"),
     Output("portfolio-holdings-table", "children"),
     Output("history-content", "children")],
    [Input("interval-component", "n_intervals"),
     Input("history-tabs", "active_tab")],
    [State("wallet-balance-store", "data"),
     State("portfolio-store", "data"),
     State("trading-history-store", "data"),
     State("wallet-history-store", "data")]
)
def update_portfolio_page(n_intervals, active_tab, balance, portfolio, trading_history, wallet_history):
    
    # --- 1. Update Wallet Balance Display ---
    wallet_display = f"₹{balance:,.2f}"

    # --- 2. Update Portfolio Holdings Table ---
    if not portfolio:
        holdings_table = dbc.Alert("You do not own any stocks.", color="info")
    else:
        portfolio_data = []
        for ticker, data in portfolio.items():
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period='1d')['Close'].iloc[-1]
                total_value = current_price * data['quantity']
                profit_loss = (current_price - data['avg_price']) * data['quantity']
                profit_loss_pct = (profit_loss / (data['avg_price'] * data['quantity'])) * 100 if data['avg_price'] > 0 else 0
                
                portfolio_data.append({
                    "Stock": ticker,
                    "Quantity": data['quantity'],
                    "Avg. Price": f"₹{data['avg_price']:,.2f}",
                    "Current Price": f"₹{current_price:,.2f}",
                    "Total Value": f"₹{total_value:,.2f}",
                    "P/L": f"₹{profit_loss:,.2f}",
                    "P/L %": f"{profit_loss_pct:.2f}%"
                })
            except Exception as e:
                print(f"Could not fetch current price for {ticker}: {e}")
                # Append with last known data if live fetch fails
                portfolio_data.append({
                    "Stock": ticker, "Quantity": data['quantity'], "Avg. Price": f"₹{data['avg_price']:,.2f}",
                    "Current Price": "N/A", "Total Value": "N/A", "P/L": "N/A", "P/L %": "N/A"
                })

        df = pd.DataFrame(portfolio_data)
        holdings_table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, dark=True)
    
    # --- 3. Update History Tabs ---
    if active_tab == "trading-history":
        if not trading_history:
            history_content = dbc.Alert("No trading history found.", color="info")
        else:
            df = pd.DataFrame(trading_history).iloc[::-1] # Reverse to show latest first
            history_content = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, dark=True)
    elif active_tab == "wallet-history":
        if not wallet_history:
            history_content = dbc.Alert("No wallet history found.", color="info")
        else:
            df = pd.DataFrame(wallet_history).iloc[::-1] # Reverse to show latest first
            history_content = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, dark=True)
            
    return wallet_display, holdings_table, history_content
