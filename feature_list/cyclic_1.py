import pandas as pd
import numpy as np

# Load data
parking_data = pd.read_csv('../parking_data-2025-01-31.csv', header=0)
event_data = pd.read_csv('../special_event_mergable-full.csv', header=0)

# Drop unnecessary column
parking_data = parking_data.drop(['ID'], axis=1)

# Create Day of Week, Month, and Hour
parking_data['Timestamp'] = pd.to_datetime(parking_data['Timestamp'])
parking_data['Day of Week'] = parking_data['Timestamp'].dt.weekday
parking_data['month'] = parking_data['Timestamp'].dt.month
parking_data['hour'] = parking_data['Timestamp'].dt.hour
parking_data['minute'] = parking_data['Timestamp'].dt.minute

# Only want testing rows
# parking_data = parking_data[parking_data['Timestamp'] > '2025-01-31 10:15:02']
parking_data = parking_data[parking_data['Timestamp'] > '2024-08-12']  # classes started 21st

# Create Total Minutes since midnight
parking_data['total_minutes'] = parking_data['hour'] * 60 + parking_data['minute']

# Apply Cyclic Encoding for Total Minutes
parking_data['time_sin'] = np.sin(2 * np.pi * parking_data['total_minutes'] / 1440)  # 1440 minutes in a day
parking_data['time_cos'] = np.cos(2 * np.pi * parking_data['total_minutes'] / 1440)

# Merge Event Data
event_data['Date'] = pd.to_datetime(event_data['Date'])
parking_data['Date'] = parking_data['Timestamp'].dt.date.astype('datetime64[ns]')  # Convert Date to datetime
parking_data = pd.merge(parking_data, event_data, on='Date', how='left')

# Drop original time-related columns
parking_data = parking_data.drop(['Timestamp', 'Date', 'total_minutes', 'hour', 'minute'], axis=1)
# parking_data = parking_data.drop(['Date', 'total_minutes', 'hour', 'minute'], axis=1)
non_nan_rows = parking_data[parking_data.notna().all(axis=1)]


parking_data = parking_data.fillna(0)

# Save to new CSV file for training
parking_data.to_csv('cyclic_1-model-small.csv', index=False)

print(parking_data.head())
print(f"Total Rows: {parking_data.shape[0]}")
