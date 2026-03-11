import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)
import matplotlib.pyplot as plt
import joblib
import time

def adjusted_mape(y_true, y_pred):
    # Avoid division by zero by replacing zero values in y_true with a small value
    nonzero_indices = y_true != 0  # Only consider values where y_true is non-zero
    y_true_nonzero = y_true[nonzero_indices]
    y_pred_nonzero = y_pred[nonzero_indices]

    # Calculate the MAPE using sklearn's implementation
    mape_value = mean_absolute_percentage_error(y_true_nonzero, y_pred_nonzero) * 100  # Convert to percentage
    
    # Return the MAPE as a percentage
    return mape_value


def eval_model(y_test, y_pred, predict_time):
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = adjusted_mape(y_test, y_pred)
    r_squared = r2_score(y_test, y_pred)
    explained_var = explained_variance_score(y_test, y_pred)

    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")
    print(f"R-squared: {r_squared:.4f}")
    print(f"Explained Variance Score: {explained_var:.4f}")
    print(f"Response Time: {predict_time:.5f}s")

model = joblib.load("best_knn.pkl")

print("Reading .csv", flush=True)
# Load cyclic class meeting times
parking_data = pd.read_csv("../d-cyclic_2-model-small.csv", header=0)
parking_data = parking_data.drop(columns=['During Standard Meeting Time?'])

X = parking_data.drop(columns=['Current Availability'])
y = parking_data['Current Availability']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Starting Predictions")
start_time = time.time()
y_pred = model.predict(X_test)
predict_time = time.time() - start_time

eval_model(y_test, y_pred, predict_time)

plt.figure(figsize=(8,6))
plt.scatter(y_test, y_pred, alpha=0.7, color='blue')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], '--', color='red')
plt.xlabel("Actual Values")
plt.ylabel("Predicted Values")
plt.title("Actual vs. Predicted Values")
plt.savefig("knn.png")
