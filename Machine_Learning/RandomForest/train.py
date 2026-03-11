import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error, r2_score
import matplotlib.pyplot as plt

# Load your parking data
parking_data = pd.read_csv("../generate_data/parking_data_feature_L6.csv", header=0)

# Convert 'Timestamp' column to datetime (if not already done)
# parking_data['Timestamp'] = pd.to_datetime(parking_data['Timestamp'])

# # Feature Engineering: Extract useful features from the Timestamp
# parking_data['day_of_week'] = parking_data['Timestamp'].dt.dayofweek  # Monday=0, Sunday=6
# parking_data['hour'] = parking_data['Timestamp'].dt.hour
# parking_data['minute'] = parking_data['Timestamp'].dt.minute

# Lag feature: Previous minute availability (assuming a single minute lag is useful)
# parking_data['lag_1'] = parking_data['Current Availability'].shift(1)

# Drop rows with missing values from the lag (if applicable)
parking_data = parking_data.dropna()

# Features (X) and Target (y)
X = parking_data.drop(columns=['Current Availability']) 
y = parking_data['Current Availability']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)  # No shuffling for time series

# Initialize the Random Forest Regressor
rf = RandomForestRegressor(n_estimators=100, random_state=42)

# Fit the model on the training data
rf.fit(X_train, y_train)

# Make predictions on the test set
y_pred = rf.predict(X_test)

# Evaluate the model
mse = root_mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print(f"Root Mean Squared Error: {rmse}")
print(f"R-squared: {r2}")

# Optionally, plot the true vs predicted values
plt.figure(figsize=(10, 6))
plt.plot(y_test.values, label='True Values')
plt.plot(y_pred, label='Predicted Values')
plt.title('Random Forest Regressor: True vs Predicted')
plt.xlabel('Time')
plt.ylabel('Parking Availability')
plt.legend()
plt.grid()
plt.show()
