# utils/data_handler.py
import yfinance as yf
import pandas as pd
from utils.ml_model import train_and_predict_svr, generate_recommendation

def fetch_stock_data(ticker, period="1y"):
    """
    Fetches historical stock data and company info for a given ticker.
    Returns (DataFrame, dict) or (None, None) if data is not found.
    """
    try:
        stock = yf.Ticker(ticker)
        # .info can be slow; consider what's essential.
        info = stock.info
        
        # Validate that we got a real company's data.
        if not info or 'longName' not in info:
            print(f"Invalid or incomplete info for ticker: {ticker}")
            return None, None

        hist = stock.history(period=period)
        if hist.empty:
            print(f"No historical data found for {ticker} for period {period}.")
            return None, None
        
        return hist, info
    except Exception as e:
        print(f"An error occurred in fetch_stock_data for {ticker}: {e}")
        return None, None

def get_key_metrics(info, stock_data):
    """
    Extracts and formats key financial metrics for the dashboard display.
    """
    # Use 'currentPrice' for more real-time data if available, else fall back.
    latest_close = info.get('currentPrice', stock_data['Close'].iloc[-1] if not stock_data.empty else 0)
    previous_close = info.get('previousClose', stock_data['Close'].iloc[-2] if len(stock_data) > 1 else 0)
    
    change = latest_close - previous_close
    percent_change = (change / previous_close * 100) if previous_close else 0
    
    currency = info.get('currency', 'USD')
    
    # Helper to format large numbers
    def format_market_cap(mc):
        if mc is None: return "N/A"
        mc = float(mc)
        if mc >= 1e12:
            return f"{mc / 1e12:.2f}T"
        elif mc >= 1e9:
            return f"{mc / 1e9:.2f}B"
        elif mc >= 1e6:
            return f"{mc / 1e6:.2f}M"
        return f"{mc:,}"

    metrics = {
        "Current Price": f"{currency} {latest_close:,.2f}",
        "Price Change": f"{change:,.2f} ({percent_change:,.2f}%)",
        "Market Cap": format_market_cap(info.get('marketCap')),
        "P/E Ratio": f"{info.get('trailingPE'):.2f}" if info.get('trailingPE') else "N/A",
        "52-Week High": f"{currency} {info.get('fiftyTwoWeekHigh', 0):,.2f}",
        "52-Week Low": f"{currency} {info.get('fiftyTwoWeekLow', 0):,.2f}",
        "Volume": f"{info.get('volume', 0):,}",
    }
    
    change_color = 'green' if change >= 0 else 'red'
    return metrics, change_color

def screen_stocks(ticker_list):
    """
    Analyzes a list of stock tickers to find potential investment opportunities.
    """
    screened_list = []
    for ticker in ticker_list:
        try:
            print(f"Screening {ticker}...")
            stock_data, stock_info = fetch_stock_data(ticker)
            if stock_data is None:
                continue

            predictions_df = train_and_predict_svr(stock_data)
            recommendation = generate_recommendation(stock_data, predictions_df)

            recommendation['Ticker'] = ticker
            recommendation['Company Name'] = stock_info.get('longName', ticker)
            recommendation['Current Price'] = f"{stock_info.get('currency', '')} {stock_data['Close'].iloc[-1]:,.2f}"

            ordered_reco = {
                'Ticker': recommendation['Ticker'],
                'Company Name': recommendation['Company Name'],
                'Recommendation': recommendation['recommendation'],
                'Current Price': recommendation['Current Price'],
                '10-Day Target': f"{stock_info.get('currency', '')} {recommendation['target_price']}",
                'Risk Level': recommendation['risk']
            }
            screened_list.append(ordered_reco)
        except Exception as e:
            print(f"Could not screen {ticker}. Error: {e}")
            continue
    return screened_list

def calculate_technical_indicators(df):
    """Calculates RSI and MACD for a given stock data DataFrame."""
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

    return df.fillna(0) # Fill NaNs that appear at the beginning of the series

def fetch_news(ticker):
    """Fetches the latest news articles for a specific stock ticker."""
    try:
        stock = yf.Ticker(ticker)
        # Limit to 5 articles for a cleaner UI
        news = stock.news[:5]
        if not news:
            return [{"title": "No recent news found for this stock."}]
        return news
    except Exception as e:
        print(f"Could not fetch news for {ticker}. Error: {e}")
        return [{"title": "Error fetching news."}]

def fetch_market_news():
    """Fetches general market news using a major index as a proxy."""
    # Using Nifty 50 for Indian market context
    nifty = yf.Ticker("^NSEI")
    try:
        news = nifty.news[:10]
        if not news:
            return [{"title": "No recent market news found."}]
        return news
    except Exception as e:
        print(f"Could not fetch market news. Error: {e}")
        return [{"title": "Error fetching market news."}]

def fetch_corporate_actions(ticker):
    """Fetches and formats dividends and stock splits for a ticker."""
    try:
        actions_df = yf.Ticker(ticker).actions
        if actions_df.empty:
            return None, None

        actions_df = actions_df.reset_index().sort_values(by='Date', ascending=False)
        actions_df['Date'] = actions_df['Date'].dt.strftime('%Y-%m-%d')

        dividends = actions_df[actions_df['Dividends'] > 0][['Date', 'Dividends']].head()
        splits = actions_df[actions_df['Stock Splits'] > 0][['Date', 'Stock Splits']].head()

        return dividends, splits
    except Exception as e:
        print(f"Could not fetch corporate actions for {ticker}. Error: {e}")
        return None, None
