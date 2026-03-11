# This data contails these fields
# Zone ID | Availability | Day of Week | Hour | Month | Event and Holiday Info | In Class Meeting Time (1/0) (no given time window)

import pandas as pd
import numpy as np

def time_str_to_float(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours + minutes / 60

def is_timestamp_in_range(time_str, time_range_str):
    time_str_float = time_str_to_float(time_str)
    start_time_str, end_time_str = time_range_str.split('-')
    start_time_str_float = time_str_to_float(start_time_str)
    end_time_str_float = time_str_to_float(end_time_str)
    return start_time_str_float <= time_str_float <= end_time_str_float, time_range_str

def is_timestamp_in_meeting_times(row):
    day_of_week = row['Day of Week']
    if day_of_week not in [5, 6]:
        meeting_times, meeting_time_gaps = meeting_times_mapping[day_of_week], meeting_time_gaps_mapping[day_of_week]
        results_meeting_times = meeting_times.apply(lambda x: is_timestamp_in_range(row['HH:MM'], x))
        results_meeting_time_gaps = meeting_time_gaps.apply(lambda x: is_timestamp_in_range(row['HH:MM'], x))
        for result, time_range_str in results_meeting_times:
            if result:
                # return True, time_range_str
                return 1
        for result, time_range_str in results_meeting_time_gaps:
            if result:
                # return False, time_range_str
                return 0
    # return False, ""
    return 0



parking_data = pd.read_csv('../parking_data.csv', header=0)
event_data = pd.read_csv('../special_event_mergable2.csv', header=0)
JMU_meeting_times = pd.read_csv('../JMU_meeting_times.csv', header=0)
JMU_meeting_time_gaps = pd.read_csv('../JMU_meeting_time_gaps.csv', header=0)

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

# Create a mapping for meeting times
meeting_times_mapping = {
    0: JMU_meeting_times['MWF'].dropna(),
    1: JMU_meeting_times['TTh'].dropna(),
    2: JMU_meeting_times['MWF'].dropna(),
    3: JMU_meeting_times['TTh'].dropna(),
    4: JMU_meeting_times['MWF'].dropna()
}

# Create a mapping for meeting time gaps
meeting_time_gaps_mapping = {
    0: JMU_meeting_time_gaps['MWF'].dropna(),
    1: JMU_meeting_time_gaps['TTh'].dropna(),
    2: JMU_meeting_time_gaps['MWF'].dropna(),
    3: JMU_meeting_time_gaps['TTh'].dropna(),
    4: JMU_meeting_time_gaps['MWF'].dropna()
}

parking_data['During Standard Meeting Time?'] = parking_data.apply(is_timestamp_in_meeting_times, axis=1)


# Create new csv to do training on
parking_data = parking_data.drop(['HH:MM', 'Timestamp', 'Date'], axis=1)
parking_data.to_csv('parking_data_feature_L6.csv', index=False)


