# utils/data_handler.py
from utils.ml_model import train_and_predict_svr, generate_recommendation
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

# Note: You'll need to import the ml_model functions at the top of data_handler.py
# from utils.ml_model import train_and_predict_svr, generate_recommendation

def screen_stocks(ticker_list):
    """
    Analyzes a list of stock tickers and returns a summary for each.
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

            # Add company name and other relevant info to the result
            recommendation['Ticker'] = ticker
            recommendation['Company Name'] = stock_info.get('longName', ticker)
            recommendation['Current Price'] = f"{stock_info.get('currency', '')} {stock_data['Close'].iloc[-1]:,.2f}"

            # Reorder dict for better table display
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
    """Calculates RSI and MACD for a given DataFrame."""
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Calculate MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

    return df
def fetch_news(ticker):
    """Fetches the latest news articles for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        # Fetch the first 5 news articles
        news = stock.news[:5]
        if not news:
            return [{"title": "No recent news found for this stock."}]
        return news
    except Exception as e:
        print(f"Could not fetch news for {ticker}. Error: {e}")
        return [{"title": "Error fetching news."}]

def fetch_market_news():
    """Fetches general market news by using a major index ticker."""
    # Using Nifty 50 as the source for general Indian market news
    nifty = yf.Ticker("^NSEI")
    try:
        # Fetch the first 10 articles
        news = nifty.news[:10]
        if not news:
            return [{"title": "No recent market news found."}]
        return news
    except Exception as e:
        print(f"Could not fetch market news. Error: {e}")
        return [{"title": "Error fetching market news."}]
