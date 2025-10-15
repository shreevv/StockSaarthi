# utils/ml_model.py
import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import RandomizedSearchCV
from datetime import timedelta
import yfinance as yf

def train_and_predict_svr(stock_data, days_to_predict=10):
    """
    Trains a Support Vector Regression (SVR) model and predicts future stock prices.
    Uses RandomizedSearchCV for hyperparameter tuning to find the best model.
    """
    if stock_data.empty or len(stock_data) < 50: # Need enough data to train
        return pd.DataFrame()

    data = stock_data.copy()
    data['Date'] = data.index
    
    # Feature Engineering: Use time-based features
    data['DayOfYear'] = data['Date'].dt.dayofyear
    data['Year'] = data['Date'].dt.year
    
    X = data[['DayOfYear', 'Year']].values
    y = data['Close'].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # SVR Hyperparameter Tuning
    param_distributions = {
        'C': [1, 10, 100, 1000],
        'gamma': np.logspace(-2, 2, 5),
        'epsilon': [0.01, 0.1, 0.5]
    }
    random_search = RandomizedSearchCV(
        SVR(kernel='rbf'),
        param_distributions,
        n_iter=10,
        cv=3,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        random_state=42
    )
    random_search.fit(X_scaled, y)
    best_svr_model = random_search.best_estimator_
    
    # Predicting future dates
    last_date = data['Date'].iloc[-1]
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_to_predict + 1)]
    future_features = np.array([[date.dayofyear, date.year] for date in future_dates])
    future_features_scaled = scaler.transform(future_features)
    predicted_prices = best_svr_model.predict(future_features_scaled)
    
    return pd.DataFrame({'Date': future_dates, 'Predicted_Close': predicted_prices})

def get_simulated_price(ticker, time_delta_days, purchase_price):
    """
    Simulates a future stock price for the "Time Travel" feature.
    This provides a more realistic price change than a simple static calculation.
    """
    try:
        # Fetch fresh data for simulation
        hist = yf.Ticker(ticker).history(period="1y")
        if hist.empty:
            # Fallback for tickers with no history
            return purchase_price * (1 + time_delta_days * 0.01)

        predictions_df = train_and_predict_svr(hist, days_to_predict=time_delta_days)
        if predictions_df.empty:
            return purchase_price * (1 + time_delta_days * 0.01)

        future_price = predictions_df['Predicted_Close'].iloc[-1]
        # Ensure a minimum positive drift to simulate general market growth
        guaranteed_price = purchase_price * (1 + time_delta_days * 0.005)
        return max(future_price, guaranteed_price)
    except Exception:
        # Generic fallback in case of API or model failure
        return purchase_price * (1 + time_delta_days * 0.01)

def generate_recommendation(stock_data, predictions_df):
    """
    Generates a Buy/Sell/Hold recommendation based on technical indicators and ML predictions.
    """
    # Simple Moving Average (SMA) Crossover Strategy
    stock_data['SMA_10'] = stock_data['Close'].rolling(window=10).mean()
    stock_data['SMA_50'] = stock_data['Close'].rolling(window=50).mean()
    last_sma_10 = stock_data['SMA_10'].iloc[-1]
    last_sma_50 = stock_data['SMA_50'].iloc[-1]
    
    # Slope of the prediction line as a momentum indicator
    prediction_slope = 0
    if not predictions_df.empty and len(predictions_df) > 1:
        prediction_slope = predictions_df['Predicted_Close'].iloc[-1] - predictions_df['Predicted_Close'].iloc[0]

    # Volatility as a risk measure
    volatility = stock_data['Close'].pct_change().dropna().std() * 100
    
    # Recommendation Logic
    recommendation = "Hold"
    if last_sma_10 > last_sma_50 and prediction_slope > 0:
        recommendation = "Buy"
    elif last_sma_10 < last_sma_50 and prediction_slope < 0:
        recommendation = "Sell"
    
    # Risk Assessment
    risk = "Medium"
    if volatility < 1.5:
        risk = "Low"
    elif volatility > 3.5:
        risk = "High"
    
    # Target Price Calculation
    target_price = 0
    if not predictions_df.empty:
        if recommendation == "Buy":
            target_price = predictions_df['Predicted_Close'].max()
        elif recommendation == "Sell":
            target_price = predictions_df['Predicted_Close'].min()
        else:
            target_price = predictions_df['Predicted_Close'].mean()
    
    return {"recommendation": recommendation, "risk": risk, "target_price": f"{target_price:,.2f}"}
