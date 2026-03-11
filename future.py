import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)
import matplotlib.pyplot as plt
import time
import joblib

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
def eval_model(y_test, y_pred, predict_time, train_time):
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
    print(f"Training Time: {train_time:.2f}s")
    print(f"Response Time: {predict_time:.5f}s")

# No Class Meeting Times
cyclic_1_model = pd.read_csv('../cyclic_1-model.csv')
cyclic_1_test = pd.read_csv('../cyclic_1-test.csv')

# Class Meeting Times
cyclic_2_model = pd.read_csv('../cyclic_2-model.csv')
cyclic_2_test = pd.read_csv('../cyclic_2-test.csv')

# Dictionary for Models for creating Data Visulazations if Needed
models = {}

# *******************
# Train Models with model dataframes
# *******************

# X and y set up
X_1 = cyclic_1_model.drop(columns=['Current Availability'])
y_1 = cyclic_1_model['Current Availability']
X_train1, X_test1, y_train1, y_test1 = train_test_split(X_1, y_1, test_size=0.1, random_state=44)

X_2 = cyclic_2_model.drop(columns=['Current Availability'])
y_2 = cyclic_2_model['Current Availability']
X_train2, X_test2, y_train2, y_test2 = train_test_split(X_2, y_2, test_size=0.1, random_state=44)


# RFR
from sklearn.ensemble import RandomForestRegressor
print("Training RFR Cyclic 1")
rfr_cyclic_1 = RandomForestRegressor(
    max_depth=20,
    min_samples_leaf=1,
    min_samples_split=2,
    n_estimators=150
)
start_time = time.time()
rfr_cyclic_1.fit(X_train1, y_train1)
train_time = time.time() - start_time
print("\tDone Training, staring predicting")
start_time = time.time()
y_pred1 = rfr_cyclic_1.predict(X_test1)
predict_time = time.time() - start_time
print("RFR No Class Meeting Times")
eval_model(y_test1, y_pred1, predict_time, train_time)
joblib.dump(rfr_cyclic_1, 'rfr_cyclic_1.pkl')
print("\tModel Saved")

print("Training RFR Cyclic 2")
rfr_cyclic_2 = RandomForestRegressor(
    max_depth=20,
    min_samples_leaf=1,
    min_samples_split=2,
    n_estimators=150
)
start_time = time.time()
rfr_cyclic_2.fit(X_train2, y_train2)
train_time = time.time() - start_time
print("\tDone Training, staring predicting")
start_time = time.time()
y_pred2 = rfr_cyclic_2.predict(X_test2)
predict_time = time.time() - start_time
print("RFR Class Meeting Times")
eval_model(y_test2, y_pred2, predict_time, train_time)
joblib.dump(rfr_cyclic_2, 'rfr_cyclic_2.pkl')
print("\tModel Saved")

# KNN
from sklearn.neighbors import KNeighborsRegressor

print("Training KNN Cyclic 1")
knn_cyclic_1 = KNeighborsRegressor(n_neighbors=2)
start_time = time.time()
knn_cyclic_1.fit(X_train1, y_train1)
train_time = time.time() - start_time
print("\tDone Training, staring predicting")
start_time = time.time()
y_pred1 = knn_cyclic_1.predict(X_test1)
predict_time = time.time() - start_time
print("KNN No Class Meeting Times")
eval_model(y_test1, y_pred1, predict_time, train_time)
joblib.dump(knn_cyclic_1, 'knn_cyclic_1.pkl')
print("\tModel Saved")

print("Training KNN Cyclic 2")
knn_cyclic_2 = KNeighborsRegressor(n_neighbors=2)
start_time = time.time()
knn_cyclic_2.fit(X_train2, y_train2)
train_time = time.time() - start_time
print("\tDone Training, staring predicting")
start_time = time.time()
y_pred2 = knn_cyclic_2.predict(X_test2)
predict_time = time.time() - start_time
print("KNN Class Meeting Times")
eval_model(y_test2, y_pred2, predict_time, train_time)
joblib.dump(knn_cyclic_2, 'knn_cyclic_2.pkl')
print("\tModel Saved")


# Predict Models with test df future results
# Function to predict future results
def predict_future(model, test_data, future_intervals):
    predictions = {}

    # Ensure Timestamp column is DateTime index
    test_data['Timestamp'] = pd.to_datetime(test_data['Timestamp'])
    test_data.set_index('Timestamp', inplace=True)

    for interval in future_intervals:
        future_time = test_data.index[0] + pd.Timedelta(minutes=interval)

        # Select the closest available time to `future_time`
        closest_time = test_data.index[test_data.index >= future_time].min()

        if pd.notna(closest_time):
            test_subset = test_data.loc[[closest_time]]

            if not test_subset.empty:
                predict_time_start = time.time()
                y_pred = model.predict(test_subset.drop(columns=['Current Availability']))
                predict_time_end = time.time()

                predictions[interval] = y_pred

                # Evaluate model
                eval_model(test_subset['Current Availability'], predictions[interval], predict_time_end - predict_time_start, 0)

                # Print actual vs predicted values
                results_df = pd.DataFrame({
                    'Actual': test_subset['Current Availability'].values,
                    'Predicted': y_pred
                })
                print(f"\nFuture Predictions vs Actual ({interval} minutes ahead):")
                print(results_df.to_string(index=False))  # Print without index for clarity

    return predictions


# Future intervals for testing
future_intervals = [
    30,     # 30 minutes
    60,     # 1 hour
    300,    # 5 hours
    720,    # 12 hours
    1440,   # 1 day
    2880,   # 2 days
    7200,   # 5 days
    10080   # 7 days (1 week)
]

# Predict and visualize results
knn_predictions_1 = predict_future(knn_cyclic_1, cyclic_1_test, future_intervals)
rfr_predictions_1 = predict_future(rfr_cyclic_1, cyclic_1_test, future_intervals)


knn_predictions_2 = predict_future(knn_cyclic_2, cyclic_2_test, future_intervals)
rfr_predictions_2 = predict_future(rfr_cyclic_2, cyclic_2_test, future_intervals)

# Visualization for cyclic_1 (No Class Meeting Times)
for interval in future_intervals:
    plt.figure(figsize=(10, 5))
    plt.plot(cyclic_1_test.index, cyclic_1_test['Current Availability'], label='Actual', linestyle='dashed')
    plt.scatter(cyclic_1_test.index, knn_predictions_1.get(interval, []), label=f'KNN {interval} min', marker='o')
    plt.scatter(cyclic_1_test.index, rfr_predictions_1.get(interval, []), label=f'RFR {interval} min', marker='x')
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("Current Availability")
    plt.title(f"No Class Meeting Times - Predictions vs Actual ({interval} min ahead)")
    plt.savefig(f"cyclic_1_full_{interval}min.png")
    plt.show()

# Visualization for cyclic_2 (Class Meeting Times)
for interval in future_intervals:
    plt.figure(figsize=(10, 5))
    plt.plot(cyclic_2_test.index, cyclic_2_test['Current Availability'], label='Actual', linestyle='dashed')
    plt.scatter(cyclic_2_test.index, knn_predictions_2.get(interval, []), label=f'KNN {interval} min', marker='o')
    plt.scatter(cyclic_2_test.index, rfr_predictions_2.get(interval, []), label=f'RFR {interval} min', marker='x')
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("Current Availability")
    plt.title(f"Class Meeting Times - Predictions vs Actual ({interval} min ahead)")
    plt.savefig(f"cyclic_2_full_{interval}min.png")
    plt.show()