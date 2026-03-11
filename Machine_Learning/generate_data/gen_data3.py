# This data contails these fields
# Zone ID | Availability | Day of Week | Hour | Month | Event and Holiday Info 

import pandas as pd
import numpy as np

parking_data = pd.read_csv('../parking_data.csv', header=0)
event_data = pd.read_csv('../special_event_mergable2.csv', header=0)

parking_data = parking_data.drop(['ID'], axis=1)

# Create Day of Week and Month and hour
parking_data['Timestamp'] = pd.to_datetime(parking_data['Timestamp'])
parking_data['Day of Week'] = parking_data['Timestamp'].dt.weekday
parking_data['HH:MM'] = parking_data['Timestamp'].dt.strftime('%H:%M')
parking_data['month'] = parking_data['Timestamp'].dt.month
parking_data['hour'] = parking_data['Timestamp'].dt.hour

# Merge Event Data
event_data['Date'] = pd.to_datetime(event_data['Date'])
parking_data['Date'] = parking_data['Timestamp'].dt.date.astype('datetime64[ns]')  # Convert Date to datetime
parking_data = pd.merge(parking_data, event_data, on='Date', how='inner')

# Create new csv to do training on
parking_data = parking_data.drop(['HH:MM', 'Timestamp', 'Date'], axis=1)
parking_data.to_csv('parking_data_feature_L3.csv', index=False)
