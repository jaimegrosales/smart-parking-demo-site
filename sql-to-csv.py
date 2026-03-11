import numpy as np
import pandas as pd
import os

sql_file = 'exported.sql'

data = []

# Open the SQL dump file
with open(sql_file, 'r') as file:
    # Read the file line by line
    for line in file:
        # Check if the line starts with "INSERT INTO"
        if line.startswith("INSERT INTO"):
            # Extract the values from the line (assuming they are comma-separated)
            values = line.split("VALUES (")[1].rstrip(");\n").split("),(")
            # Parse each value and append it to the data list
            for value in values:
                data.append(tuple(value.strip("()").split(",")))

# Define column names
columns = ['ID', 'Zone', 'Timestamp', 'Current Availability']
# Create DataFrame
df = pd.DataFrame(data, columns=columns)

# Convert 'Timestamp' column to DateTime format
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

df = df[df['Timestamp'] > '2024-08-17']
# save to csv
df.to_csv('parking_data.csv', index=False)