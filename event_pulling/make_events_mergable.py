import pandas as pd

df = pd.read_csv('special_events2.csv')

# Create Date object so can merge on Date
df['Date'] = pd.to_datetime(df['Event DateTime'], format='%m/%d/%Y %I:%M:%S %p').dt.strftime('%m/%d/%Y')

# Make Pivot Table
df_pivot = pd.pivot_table(df, index='Date', columns='Title', aggfunc='size', fill_value=0)
df_pivot.to_csv('special_event_mergable2.csv')