import pandas as pd
import numpy as np

og_df = pd.read_csv("../Train_cleaned.csv")
og_df = og_df.drop(columns=['Unnamed: 0'])

# Drop all rows where there are no events recorded
    # Ash Wednesday,Commencement,Easter Sunday,Exam Week,Fall Break,Family Weekend,
    # Home Football Game,Home Football Game (Homecoming),Independence Day,Juneteenth,
    # Labor Day,Martin Luther King Jr. Day,Memorial Day,Spring Break,St. Patrick&#39;s Day,
    # Thanksgiving Break,Winter Break
event_columns = ['Ash Wednesday', 'Commencement', 'Easter Sunday', 'Exam Week', 'Fall Break', 'Family Weekend',
    'Home Football Game', 'Home Football Game (Homecoming)', 'Independence Day', 'Juneteenth',
    'Labor Day', 'Martin Luther King Jr. Day', 'Memorial Day', 'Spring Break', 'St. Patrick&#39;s Day',
    'Thanksgiving Break', 'Winter Break']
events_df = og_df[og_df[event_columns].any(axis=1)]

no_events_df = og_df[~og_df[event_columns].any(axis=1)]

print(events_df.head(5))
print(no_events_df.head(5))

events_df.to_csv('events_data.csv', index=False)
no_events_df.to_csv('no_events_data.csv', index=False)