
import gcsfs
import dask.dataframe as dd
import pandas as pd

# Initialize Google Cloud Storage FileSystem
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Load the dataset from Google Cloud Storage
df = dd.read_csv("gs://airport-weather-data/airport-weather-data.csv", storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

# Select only the necessary columns
df_subset = df[['OriginAirportID', 'DestAirportID', 'Distance']].drop_duplicates()

# Convert Dask DataFrame to Pandas DataFrame
df_subset_pd = df_subset.compute()

# Save to a single CSV locally
local_output_path = "origin_dest_distance.csv"
df_subset_pd.to_csv(local_output_path, index=False)

print("Local CSV file with all OriginAirportID-DestAirportID-Distance combinations has been saved.")
