import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import time
import joblib
from tensorflow.keras.models import load_model

def adjusted_mape(y_true, y_pred):
    # Avoid division by zero by replacing zero values in y_true with a small value
    nonzero_indices = y_true != 0  # Only consider values where y_true is non-zero
    y_true_nonzero = y_true[nonzero_indices]
    y_pred_nonzero = y_pred[nonzero_indices]

    # Calculate the MAPE using sklearn's implementation
    mape_value = mean_absolute_percentage_error(y_true_nonzero, y_pred_nonzero) * 100  # Convert to percentage

    # Return the MAPE as a percentage
    return mape_value

# Evaluate the model method
def eval_model(y_test, y_pred, predict_time):
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = adjusted_mape(y_test, y_pred)
    r_squared = r2_score(y_test, y_pred)
    explained_var = explained_variance_score(y_test, y_pred)

    print(f"\tRoot Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"\tMean Absolute Error (MAE): {mae:.4f}")
    print(f"\tMean Absolute Percentage Error (MAPE): {mape:.2f}%")
    print(f"\tR-squared: {r_squared:.4f}")
    print(f"\tExplained Variance Score: {explained_var:.4f}")
    print(f"Response Time: {predict_time:.5f}s")

# No Class Meeting Times
cyclic_1_test = pd.read_csv('cyclic_1-test.csv')

# Predict Models with test df future results
# Function to predict future results
def predict_future(model, test_data):
    # Ensure Timestamp column is DateTime index
    test_data['Timestamp'] = pd.to_datetime(test_data['Timestamp'])
    
    X_test = test_data.drop(columns=['Current Availability', 'Timestamp'])
    
    # Make predictions
    start_time = time.time()
    y_pred = model.predict(X_test)
    p_time = time.time() - start_time
    
    # create results dataframe
    results_df = pd.DataFrame({
        'Zone': test_data['Zone'],
        'Timestamp': test_data['Timestamp'],
        'Actual': test_data['Current Availability'],
        'Predicted': y_pred
    })
    eval_model(results_df['Actual'], results_df['Predicted'], p_time)

    return results_df
    
def predict_future_lstm(model, test_data):
    scaler = MinMaxScaler(feature_range=(0,1))
    
    # Ensure Timestamp column is DateTime index
    test_data['Timestamp'] = pd.to_datetime(test_data['Timestamp'])
    
    X_test = test_data.drop(columns=['Current Availability', 'Timestamp'])
    
    X_test_scaled = scaler.fit_transform(X_test)
    X_test_reshaped = np.reshape(X_test_scaled, (X_test_scaled.shape[0], 1, X_test_scaled.shape[1]))
    
    # Make predictions
    start_time = time.time()
    y_pred = model.predict(X_test_reshaped)
    y_pred = y_pred.flatten()
    p_time = time.time() - start_time
    
    # Create results dataframe
    results_df = pd.DataFrame({
        'Zone': test_data['Zone'],
        'Timestamp': test_data['Timestamp'],
        'Actual': test_data['Current Availability'],
        'Predicted': y_pred
    })
    eval_model(results_df['Actual'], results_df['Predicted'], p_time)
    
    return results_df
    

# Predict and visualize results
print("KNN", flush=True)
knn = joblib.load("../knn/knn_semi.pkl")
knn_predictions = predict_future(knn, cyclic_1_test)
knn_predictions.to_csv("knn_predictions.csv", index=False)

print("RFR", flush=True)
rfr = joblib.load("../rfr/rfr_semi.pkl")
rfr_predictions = predict_future(rfr, cyclic_1_test)
rfr_predictions.to_csv("rfr_predictions.csv", index=False)

print("LSTM", flush=True)
lstm = load_model("../lstm/lstm_semi.h5")
lstm_predictions = predict_future_lstm(lstm, cyclic_1_test)
lstm_predictions.to_csv("lstm_predictions.csv", index=False)

print("LSTM Large", flush=True)
lstm_large = load_model("../lstm/lstm_large.h5")
lstm_large_predictions = predict_future_lstm(lstm_large, cyclic_1_test)
lstm_large_predictions.to_csv("lstm_large_predictions.csv", index=False)


# Visualization for cyclic_1 (No Class Meeting Times)


