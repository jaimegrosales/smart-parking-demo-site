from scikeras.wrappers import KerasRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, train_test_split
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, Input
from keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)

policy = tf.keras.mixed_precision.Policy('mixed_float16')
tf.keras.mixed_precision.set_global_policy(policy)

def adjusted_mape(y_true, y_pred):
    nonzero_indices = y_true != 0
    y_true_nonzero = y_true[nonzero_indices]
    y_pred_nonzero = y_pred[nonzero_indices]
    mape_value = mean_absolute_percentage_error(y_true_nonzero, y_pred_nonzero) * 100
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

def build_model(units=100, dropout_rate=0.3, input_shape=None):
    model = Sequential()
    model.add(Input(shape=input_shape))
    model.add(LSTM(units=units, return_sequences=True))
    model.add(Dropout(dropout_rate))
    model.add(LSTM(units=units, return_sequences=False))
    model.add(Dropout(dropout_rate))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# Early stopping
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

print("Reading .csv", flush=True)
# Load cyclic class meeting times
parking_data = pd.read_csv("../large_semi_cyclic.csv", header=0)

X = parking_data.drop(columns=['Current Availability'])
y = parking_data['Current Availability']

# Split dataset into train and testing sets
X_train1, X_test1, y_train1, y_test1 = train_test_split(X, y, test_size=0.2, random_state=44)

scaler = MinMaxScaler(feature_range=(0,1))
X_train_scaled1 = scaler.fit_transform(X_train1)
X_test_scaled1 = scaler.transform(X_test1)

# reshape data for LSTM (samples, timesteps, features)
X_train_scaled1 = np.reshape(X_train_scaled1, (X_train_scaled1.shape[0], 1, X_train_scaled1.shape[1]))  # Timesteps = 1
X_test_scaled1 = np.reshape(X_test_scaled1, (X_test_scaled1.shape[0], 1, X_test_scaled1.shape[1]))  # Timesteps = 1

shape = X_train_scaled1.shape[1:]

# Wrap the model with KerasRegressor and ensure it is treated as a regressor
best_model = KerasRegressor(build_fn=build_model, input_shape=shape, verbose=0)

print("Training Model")
best_model.fit(
    X_train_scaled1, y_train1, 
    epochs=150, 
    batch_size=64,
    validation_data=(X_test_scaled1, y_test1), 
    callbacks=[early_stopping]
)

print("Predicting")
# Predict on the test data
y_pred = best_model.predict(X_test_scaled1)

# Save the best model
best_model.model_.save('lstm_large.h5')

# Evaluate the model
eval(y_test1, y_pred)

# Plot the results
plt.figure(figsize=(8,6))
plt.scatter(y_test1, y_pred, alpha=0.7, color='blue')
plt.plot([y_test1.min(), y_test1.max()], [y_test1.min(), y_test1.max()], '--', color='red')
plt.xlabel("Actual Values")
plt.ylabel("Predicted Values")
plt.title("Actual vs. Predicted Values")
plt.savefig("lstm_large.png")

