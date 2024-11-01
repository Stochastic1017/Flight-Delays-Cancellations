
import pandas as pd
import os

# Define the directory and columns to keep
directory = "merge/"
columns_to_keep = [
    'DATE',
    'HourlyDryBulbTemperature', 
    'HourlyWindSpeed', 
    'HourlyWindDirection', 
    'HourlyDewPointTemperature', 
    'HourlyRelativeHumidity', 
    'HourlyVisibility', 
    'HourlyStationPressure', 
    'HourlyWetBulbTemperature', 
    'HourlySkyConditions'
]

# Loop through each file in the directory
for filename in os.listdir(directory):
    if filename.endswith(".csv"):
        filepath = os.path.join(directory, filename)
        
        # Read and filter the DataFrame
        df = pd.read_csv(filepath, low_memory=False)
        df_filtered = df.filter(columns_to_keep, axis=1)
        
        # Overwrite the original CSV with the filtered DataFrame
        df_filtered.to_csv(filepath, index=False)
