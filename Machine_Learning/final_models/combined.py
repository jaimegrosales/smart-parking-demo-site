# Run all Here
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, TimeSeriesSplit
from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)
import joblib
import time

# For KNN
from sklearn.neighbors import KNeighborsRegressor

# For ELNET
from sklearn.linear_model import ElasticNet

# For RF Regressor
from sklearn.ensemble import RandomForestRegressor

# For LSTM
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, Input
from keras.callbacks import EarlyStopping
from scikeras.wrappers import KerasRegressor

def adjusted_mape(y_true, y_pred):
    # Avoid division by zero by replacing zero values in y_true with a small value
    nonzero_indices = y_true != 0  # Only consider values where y_true is non-zero
    y_true_nonzero = y_true[nonzero_indices]
    y_pred_nonzero = y_pred[nonzero_indices]

    # Calculate the MAPE using sklearn's implementation
    mape_value = mean_absolute_percentage_error(y_true_nonzero, y_pred_nonzero) * 100  # Convert to percentage
    
    # Return the MAPE as a percentage
    return mape_value
    
def eval(y_test, y_pred):
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = adjusted_mape(y_test, y_pred)
    r_squared = r2_score(y_test, y_pred)
    ev = explained_variance_score(y_test, y_pred)

    print(f"\tRMSE: {rmse:.4f}")
    print(f"\tMAE: {mae:.4f}")
    print(f"\tMAPE: {mape:.2f}%")
    print(f"\tr2: {r_squared:.4f}")
    print(f"\tev: {ev:.4f}", flush=True)
    return

print("Reading .csv", flush=True)
# Load cyclic class meeting times
parking_data = pd.read_csv("cleaned_pd.csv", header=0)
#parking_data = parking_data.drop(columns=['During Standard Meeting Time?'])

X = parking_data.drop(columns=['Current Availability'])
y = parking_data['Current Availability']

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# KNN Training
print("\nKNN", flush=True)

# Perform Grid Search for the best 'n_neighbors'
param_grid = {
    'n_neighbors': list(range(1,30)),
    'algorithm': ['ball_tree'],
    'n_jobs': [-1]
}

grid_search = GridSearchCV(KNeighborsRegressor(), param_grid, cv=TimeSeriesSplit(n_splits=5), scoring='neg_mean_squared_error')

print("Starting Training", flush=True)
grid_search.fit(X_train, y_train)
print("Finished Training", flush=True)

# Best Parameters and model
best_params = grid_search.best_params_
knn = grid_search.best_estimator_
y_pred = knn.predict(X_test)

joblib.dump(knn, "best_knn.pkl")
print("Model saved", flush=True)
print("\tBest Parameters:", best_params)
eval(y_test, y_pred)

# RFR
print("\nRFR", flush=True)

param_grid = {
    'n_estimators': [150],
    'max_depth': [15, 20],
    'min_samples_split': [2],
    'min_samples_leaf': [1]
}
grid_search = GridSearchCV(
    estimator=RandomForestRegressor(),
    param_grid=param_grid,
    cv=TimeSeriesSplit(n_splits=3),
    scoring='neg_mean_squared_error',
    n_jobs=-1
)

print("Starting Training", flush=True)
grid_search.fit(X_train, y_train)
print("Finished Training", flush=True)

rf_best = grid_search.best_estimator_
best_params = grid_search.best_params_
y_pred = rf_best.predict(X_test)
joblib.dump(rf_best, "best_rfr.pkl")
print("Model saved", flush=True)
print("\tBest Parameters:", best_params)
eval(y_test, y_pred)


