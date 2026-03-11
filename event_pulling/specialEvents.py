import pandas as pd

df = pd.read_csv('calendar_events-full.csv')

# Normalize the 'Special?' column for robust filtering
special_mask = df['Special?'].astype(str).str.strip().str.lower() == 'true'
new_df = df[special_mask]

new_df.to_csv('special_events2.csv', index=False)