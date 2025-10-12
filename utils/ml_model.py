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
    Trains an SVR model using RandomizedSearchCV for hyperparameter tuning 
    and predicts future prices.
    """
    if stock_data.empty:
        return pd.DataFrame()

    # --- 1. Feature Engineering ---
    data = stock_data.copy()
    data['Date'] = data.index
    data['DayOfYear'] = data['Date'].dt.dayofyear
    data['Year'] = data['Date'].dt.year
    
    X = data[['DayOfYear', 'Year']].values
    y = data['Close'].values

    # --- 2. Data Scaling ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- 3. UPDATED: Hyperparameter Tuning with RandomizedSearchCV ---
    # Define a range of parameters to test.
    param_distributions = {
        'C': [1, 10, 100, 1000],
        'gamma': np.logspace(-2, 2, 5), # values from 0.01 to 100
        'epsilon': [0.01, 0.1, 0.5]
    }

    # Create the RandomizedSearchCV object.
    # n_iter controls how many different parameter combinations are tested.
    # cv is the number of cross-validation folds.
    # n_jobs=-1 uses all available CPU cores to speed up the search.
    random_search = RandomizedSearchCV(
        SVR(kernel='rbf'),
        param_distributions=param_distributions,
        n_iter=10,
        cv=3,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        random_state=42
    )
    
    # Fit the model. This will automatically find the best parameters from the list.
    random_search.fit(X_scaled, y)
    
    # The best model found by the search.
    best_svr_model = random_search.best_estimator_
    print(f"Best SVR params found: {random_search.best_params_}")

    # --- 4. Future Prediction (using the best model) ---
    last_date = data['Date'].iloc[-1]
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_to_predict + 1)]
    future_features = np.array([[date.dayofyear, date.year] for date in future_dates])
    future_features_scaled = scaler.transform(future_features)
    
    # Predict using the optimized model.
    predicted_prices = best_svr_model.predict(future_features_scaled)
    
    # --- 5. Format the Output ---
    predictions_df = pd.DataFrame({
        'Date': future_dates,
        'Predicted_Close': predicted_prices
    })
    
    return predictions_df

# The other two functions, get_simulated_price and generate_recommendation, remain unchanged.
# For a complete working file, you must include the full code for those two functions here.
# ... (get_simulated_price function from Part 9) ...
# ... (generate_recommendation function from Part 11) ...
