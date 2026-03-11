import pandas as pd
import numpy as np

no_events = pd.read_csv('../events_models/no_events_data.csv')

# June (6) - August (8)
summer = no_events[no_events['month'].isin([6, 7, 8])]

print(summer['month'].unique())
summer.to_csv('summer_data.csv', index=False)