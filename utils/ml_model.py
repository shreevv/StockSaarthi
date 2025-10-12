# utils/ml_model.py

import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from datetime import timedelta

def train_and_predict_svr(stock_data, days_to_predict=10):
    """
    Trains an SVR model on historical stock data and predicts future prices.

    Args:
        stock_data (pd.DataFrame): DataFrame with historical stock data. Must have a 'Close' column.
        days_to_predict (int): The number of future days to predict.

    Returns:
        pd.DataFrame: A DataFrame with future dates and their predicted prices.
    """
    if stock_data.empty:
        return pd.DataFrame()

    # --- 1. Feature Engineering ---
    # We create features for the model to learn from.
    data = stock_data.copy()
    data['Date'] = data.index
    data['Day'] = data['Date'].dt.day
    data['Month'] = data['Date'].dt.month
    data['Year'] = data['Date'].dt.year

    # We'll use the day of the year as our main numerical feature for time.
    data['DayOfYear'] = data['Date'].dt.dayofyear

    # Features (X) and Target (y)
    X = data[['DayOfYear', 'Year']].values
    y = data['Close'].values

    # --- 2. Data Scaling ---
    # SVR is sensitive to feature scaling, so we normalize our data.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- 3. Model Training ---
    # We'll use a Radial Basis Function (RBF) kernel for our SVR model.
    # These hyperparameters (C, gamma, epsilon) are a good starting point.
    svr_model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.1)
    svr_model.fit(X_scaled, y)

    # --- 4. Future Prediction ---
    # Create features for the future days we want to predict.
    last_date = data['Date'].iloc[-1]
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_to_predict + 1)]

    future_features = np.array([[date.dayofyear, date.year] for date in future_dates])

    # Scale the future features using the same scaler we trained on.
    future_features_scaled = scaler.transform(future_features)

    # Predict the future prices.
    predicted_prices = svr_model.predict(future_features_scaled)

    # --- 5. Format the Output ---
    predictions_df = pd.DataFrame({
        'Date': future_dates,
        'Predicted_Close': predicted_prices
    })

    return predictions_df
def get_simulated_price(ticker, time_delta_days, purchase_price):
    """
    Generates a simulated future price for a stock, ensuring it's profitable.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty:
            # If no history, return a simple profitable price
            return purchase_price * (1 + time_delta_days * 0.01) # 1% gain per day

        # Get the SVR prediction
        predictions_df = train_and_predict_svr(hist, days_to_predict=time_delta_days)
        if predictions_df.empty:
            return purchase_price * (1 + time_delta_days * 0.01)

        # Get the predicted price for the specific future day
        future_price = predictions_df['Predicted_Close'].iloc[-1]

        # **Demonstration Logic**: Ensure the future price is always profitable
        # We'll set a minimum gain of 0.5% per day from the purchase price
        guaranteed_price = purchase_price * (1 + time_delta_days * 0.005)

        # The final simulated price will be the higher of the prediction or the guaranteed price
        simulated_price = max(future_price, guaranteed_price)

        return simulated_price
    except Exception:
        # Fallback for any errors
        return purchase_price * (1 + time_delta_days * 0.01)

def generate_recommendation(stock_data, predictions_df):
    """
    Generates a trading recommendation based on historical trends and SVR predictions.
    """
    # --- 1. Trend Analysis (Moving Averages) ---
    # A "golden cross" (short-term avg > long-term avg) is a bullish signal.
    # A "death cross" (short-term avg < long-term avg) is a bearish signal.
    stock_data['SMA_10'] = stock_data['Close'].rolling(window=10).mean()
    stock_data['SMA_50'] = stock_data['Close'].rolling(window=50).mean()
    last_sma_10 = stock_data['SMA_10'].iloc[-1]
    last_sma_50 = stock_data['SMA_50'].iloc[-1]

    # --- 2. Prediction Slope Analysis ---
    # Is the SVR model predicting an upward or downward trend?
    if not predictions_df.empty:
        prediction_slope = predictions_df['Predicted_Close'].iloc[-1] - predictions_df['Predicted_Close'].iloc[0]
    else:
        prediction_slope = 0

    # --- 3. Volatility Analysis (for Risk) ---
    # We calculate the standard deviation of daily returns as a proxy for risk.
    daily_returns = stock_data['Close'].pct_change().dropna()
    volatility = daily_returns.std() * 100 # In percentage terms

    # --- 4. Recommendation Logic ---
    recommendation = "Hold"
    if last_sma_10 > last_sma_50 and prediction_slope > 0:
        recommendation = "Buy"
    elif last_sma_10 < last_sma_50 and prediction_slope < 0:
        recommendation = "Sell"

    # --- 5. Risk Logic ---
    risk = "Medium"
    if volatility < 1.5:
        risk = "Low"
    elif volatility > 3.5:
        risk = "High"

    # --- 6. Target Price Logic ---
    target_price = 0
    if not predictions_df.empty:
        if recommendation == "Buy":
            target_price = predictions_df['Predicted_Close'].max()
        elif recommendation == "Sell":
            target_price = predictions_df['Predicted_Close'].min()
        else:
            target_price = predictions_df['Predicted_Close'].mean()

    return {
        "recommendation": recommendation,
        "risk": risk,
        "target_price": f"{target_price:,.2f}"
    }
