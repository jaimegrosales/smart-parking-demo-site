# This data contails these fields
# Zone ID | Availability | Day of Week | Time (Minutes from Midnight) | Month | Event and Holiday Info 

import pandas as pd
import numpy as np

parking_data = pd.read_csv('../parking_data-2024-09-25.csv', header=0)
zone_max_availability = pd.read_csv('../max_availability_per_zone.csv', header=0)
event_data = pd.read_csv('../special_event_mergable.csv', header=0)

# Grab only the wanted zone id for the model | may change later to include all zones?
parking_data = parking_data.drop(['ID'], axis=1)
# parking_data = parking_data[parking_data['Zone'] == 6]
parking_data = pd.merge(parking_data, zone_max_availability[['Zone', 'Max Availability']], how='left', on='Zone')

# Create availability ratio
# availability_ratio_values = ((parking_data['Max Availability'] - parking_data['Current Availability']) / parking_data['Max Availability'])
# parking_data['Availability Ratio'] = availability_ratio_values

# Create Day of Week
parking_data['Timestamp'] = pd.to_datetime(parking_data['Timestamp'])
parking_data['Day of Week'] = parking_data['Timestamp'].dt.weekday
parking_data['HH:MM'] = parking_data['Timestamp'].dt.strftime('%H:%M')

# Create Time, Month
parking_data['time'] = parking_data['Timestamp'].dt.strftime('%H:%M')
parking_data['time'] = pd.to_datetime(parking_data['time'], format='%H:%M').dt.hour * 60 + pd.to_datetime(parking_data['time'], format='%H:%M').dt.minute
parking_data['month'] = parking_data['Timestamp'].dt.month

# Merge Event Data
event_data['Date'] = pd.to_datetime(event_data['Date'])
parking_data['Date'] = parking_data['Timestamp'].dt.date.astype('datetime64[ns]')  # Convert Date to datetime

# Merge Event Data
parking_data = pd.merge(parking_data, event_data, on='Date', how='inner')

# Create new csv to do training on
parking_data = parking_data.drop(['Max Availability', 'HH:MM', 'Date'], axis=1)
parking_data.to_csv('09-25-2024_feature_L2.csv', index=False)

