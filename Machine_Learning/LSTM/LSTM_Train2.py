import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import root_mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt

# Load the dataset
dataset = pd.read_csv('09-25-2024-2.csv')

# Feature Engineering: Extract useful time-based features from Timestamp
dataset['Timestamp'] = pd.to_datetime(dataset['Timestamp'])  # Ensure Timestamp is in datetime format
dataset['hour'] = dataset['Timestamp'].dt.hour
dataset['day_of_week'] = dataset['Timestamp'].dt.dayofweek
dataset['day_of_month'] = dataset['Timestamp'].dt.day
dataset['month'] = dataset['Timestamp'].dt.month

# Drop the original 'Timestamp' as it won't be used directly in the model
X = dataset.drop(columns=['Current Availability', 'Timestamp'])
y = dataset['Current Availability']

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the data (important for LSTM models)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Reshape the data for LSTM (samples, timesteps, features)
X_train_scaled = np.reshape(X_train_scaled, (X_train_scaled.shape[0], 1, X_train_scaled.shape[1]))
X_test_scaled = np.reshape(X_test_scaled, (X_test_scaled.shape[0], 1, X_test_scaled.shape[1]))

# Build the LSTM model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True))
model.add(LSTM(units=50))
model.add(Dense(units=1))  # Output layer

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Define EarlyStopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# Train the model
history = model.fit(X_train_scaled, y_train, epochs=100, batch_size=32, validation_data=(X_test_scaled, y_test), callbacks=[early_stopping])

# Predictions
y_pred = model.predict(X_test_scaled)
print(f"NaN in y_test: {np.isnan(y_test).sum()}")
print(f"NaN in y_pred: {np.isnan(y_pred).sum()}")


# Calculate RMSE
rmse = np.sqrt(root_mean_squared_error(y_test, y_pred))
print(f'Root Mean Squared Error: {rmse}')

# Plot Training and Validation Loss
plt.figure(figsize=(10, 6))
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Training and Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.ylim([0, 1000])  # Adjust y-axis limits to zoom in
plt.show()

# Plot Predicted vs Actual Values
# plt.figure(figsize=(10, 6))
# plt.plot(y_test.values, label='Actual Values', color='blue')
# plt.plot(y_pred, label='Predicted Values', color='red')
# plt.title('Actual vs Predicted Current Availability')
# plt.xlabel('Samples')
# plt.ylabel('Current Availability')
# plt.legend()
# plt.show()
