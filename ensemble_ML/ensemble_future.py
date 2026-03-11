import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)
import joblib
import time
from joblib import Parallel, delayed

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
    

# Predict Models with test df future results
# Function to predict future results
def predict_future(test_data):
    # Ensure Timestamp column is DateTime index
    test_data['Timestamp'] = pd.to_datetime(test_data['Timestamp'])
    
    X_test = test_data.drop(columns=['Current Availability', 'Timestamp'])
    
    # Make predictions
    start_time = time.time()
    y_pred = ensemble_predict(X_test)
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
    
# Event Columns
event_columns = ['Ash Wednesday', 'Commencement', 'Easter Sunday', 'Exam Week', 'Fall Break', 'Family Weekend',
                'Home Football Game', 'Home Football Game (Homecoming)', 'Independence Day', 'Juneteenth',
                'Labor Day', 'Martin Luther King Jr. Day', 'Memorial Day', 'Spring Break', 'St. Patrick&#39;s Day',
                'Thanksgiving Break', 'Winter Break']

def classify_rows(X_test):
    event_mask = X_test[event_columns].sum(axis=1) > 0
    summer_mask = X_test['month'].isin([6, 7, 8]) & ~event_mask
    school_mask = ~event_mask & ~summer_mask

    return event_mask, summer_mask, school_mask
    
def ensemble_predict(X_test):
    pred = np.empty(len(X_test))  # Create an array to store predictions in original order

    event_mask, summer_mask, school_mask = classify_rows(X_test)

    X_event = X_test[event_mask]
    X_summer = X_test[summer_mask].drop(columns=event_columns, errors='ignore')
    X_school = X_test[school_mask].drop(columns=event_columns, errors='ignore')

    if not X_event.empty:
        pred[event_mask] = events_model.predict(X_event)
    if not X_school.empty:
        pred[school_mask] = school_model.predict(X_school)
    if not X_summer.empty:
        pred[summer_mask] = summer_model.predict(X_summer)

    return pred
    
    
# Load Models
events_model = joblib.load('../events_models/best_events_knn.pkl')
summer_model = joblib.load('../summer_models/best_summer_knn.pkl')
school_model = joblib.load('../schoolYear_models/best_school_knn.pkl')

# Load Future Data
cyclic_1_test = pd.read_csv('cyclic_1-test.csv')
cyclic_1_test['Timestamp'] = pd.to_datetime(cyclic_1_test['Timestamp'])
cyclic_1_test = cyclic_1_test[~((cyclic_1_test['Timestamp'].dt.month == 2) & (cyclic_1_test['Timestamp'].dt.day == 1))]

# Predict and Visualize Results
print("Ensemble", flush=True)
predictions = predict_future(cyclic_1_test)
predictions.to_csv("future_predictions.csv", index=False)









