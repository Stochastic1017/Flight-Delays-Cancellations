
import gcsfs
import dask.dataframe as dd
import pandas as pd

# Initialize Google Cloud Storage FileSystem
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Load merged dataset and airport metadata
df = dd.read_csv("gs://airport-weather-data/airport-weather-data.csv", storage_options={"token": "flights-weather-project-f94d306bee1f.json"})
df_airport = dd.read_csv("gs://airport-weather-data/airports-list-us.csv", storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Extract unique airline options
airlines = df['Marketing_Airline_Network'].drop_duplicates().compute()

# Extract unique airport options with correct metadata
# Merge on 'AIRPORT_ID' to keep associations intact
airport_metadata = (
    df_airport[['AIRPORT_ID', 'DISPLAY_AIRPORT_NAME', 'AIRPORT']]
    .drop_duplicates(subset='AIRPORT_ID')  # Ensure each airport ID is unique
    .compute()
)

# Prepare data in a structure suitable for dropdowns
# Ensure the lists are of equal length and match 'AIRPORT_ID' with corresponding names and codes
data = {
    "airline": airlines,
    "airport_id": airport_metadata['AIRPORT_ID'],
    "airport_display_name": airport_metadata['DISPLAY_AIRPORT_NAME'],
    "airport_code": airport_metadata['AIRPORT']
}

# Convert to DataFrame and save to CSV
options_df = pd.DataFrame(data)
options_df.to_csv("options_for_prediction.csv", index=False)

print("Options CSV for prediction created successfully, with accurate airline and airport metadata.")
