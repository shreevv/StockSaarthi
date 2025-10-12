# utils/data_handler.py

import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, period="1y"):
    """
    Fetches historical stock data for a given ticker.
    Returns a pandas DataFrame and the company's info dictionary.
    Returns (None, None) if the ticker is invalid or data is not found.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or info.get('trailingPE') is None:
            print(f"Info dictionary is incomplete or invalid for {ticker}.")
            return None, None

        hist = stock.history(period=period)
        if hist.empty:
            print(f"No historical data found for {ticker} for the period {period}.")
            return None, None
        
        return hist, info
    except Exception as e:
        print(f"An error occurred while fetching data for {ticker}: {e}")
        return None, None

def get_key_metrics(info, stock_data):
    """
    Extracts and formats key financial metrics from yfinance info and history.
    """
    latest_close = stock_data['Close'].iloc[-1] if not stock_data.empty else info.get('previousClose')
    previous_close = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else info.get('open')
    
    change = latest_close - previous_close if latest_close and previous_close else 0
    percent_change = (change / previous_close * 100) if previous_close else 0
    
    currency = info.get('currency', 'USD')
    
    metrics = {
        "Current Price": f"{currency} {latest_close:,.2f}" if latest_close else "N/A",
        "Price Change": f"{change:,.2f} ({percent_change:,.2f}%)",
        "Market Cap": f"{currency} {info.get('marketCap', 0):,}" if info.get('marketCap') else "N/A",
        "P/E Ratio": f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A",
        "52-Week High": f"{currency} {info.get('fiftyTwoWeekHigh', 0):,.2f}" if info.get('fiftyTwoWeekHigh') else "N/A",
        "52-Week Low": f"{currency} {info.get('fiftyTwoWeekLow', 0):,.2f}" if info.get('fiftyTwoWeekLow') else "N/A",
        "Volume": f"{info.get('volume', 0):,}" if info.get('volume') else "N/A",
        "Avg. Volume": f"{info.get('averageVolume', 0):,}" if info.get('averageVolume') else "N/A",
    }
    
    change_color = 'green' if change >= 0 else 'red'
    
    return metrics, change_color