
import pandas as pd
import gcsfs
import dask.dataframe as dd

# Initialize Google Cloud Storage FileSystem
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Load large dataset from Google Cloud Storage
df = dd.read_csv(
    "gs://airport-weather-data/airport-weather-data.csv", 
    storage_options={"token": "flights-weather-project-f94d306bee1f.json"}
)

# Columns in the dataset
print(df.columns)

# Calculate metrics for each airport
metrics_df = df.groupby("OriginAirportID").agg({
    "Cancelled": "mean",  # Cancellation rate
    "ArrivalDelay": "mean",  # Average arrival delay
    "DepartureDelay": "mean",  # Average departure delay
    "TotalFlightDelay": "mean",  # Average total flight delay
    "TaxiDelay": "mean"  # Average taxi delay
}).compute()

# Rename columns for clarity
metrics_df = metrics_df.rename(columns={
    "Cancelled": "CancellationRate",
    "ArrivalDelay": "AvgArrivalDelay",
    "DepartureDelay": "AvgDepartureDelay",
    "TotalFlightDelay": "AvgTotalFlightDelay",
    "TaxiDelay": "AvgTaxiDelay"
}).reset_index()

# Load airport metadata for name lookup
airport_metadata = "gs://airport-weather-data/airports-list-us.csv"
df_airport = pd.read_csv(
    airport_metadata,
    storage_options={"token": "flights-weather-project-f94d306bee1f.json"},
)

# Merge metrics with airport metadata
df_airport = df_airport.merge(
    metrics_df,
    left_on="AIRPORT_ID",
    right_on="OriginAirportID",
    how="left"
)

# Check the updated df_airport with the new columns added
print(df_airport.iloc[: , 1:])
df_airport.iloc[: , 1:].to_csv("airports-list-us.csv", index=False)
