
import os
from glob import glob
import pandas as pd
import reverse_geocoder as rg
import ast

# Function to safely parse coordinates
def parse_coord(item):
    try:
        # Attempt to parse and return as tuple of floats
        return ast.literal_eval(item)
    except (ValueError, SyntaxError):
        # Return None if the format is incorrect
        return None
    
# Change directory to the folder containing CSV files
os.chdir("/home/stochastic1017/Documents/Flight-Delays-Cancellations/2023")
files = glob("*.csv")

# Initialize lists to collect data
coords = []
station_name = []
elevation = []

# Process each CSV file
for i, file in enumerate(files):
    print(f"Currently at file: {file}. At: {i + 1} out of {len(files)}")
    df = pd.read_csv(file, low_memory=False)
    
    # Collect latitude, longitude, station name, and elevation
    coords.append((df["LATITUDE"][0], df["LONGITUDE"][0]))
    station_name.append(df["NAME"][0])
    elevation.append(df["ELEVATION"][0])

# Change back to the main directory
os.chdir("/home/stochastic1017/Documents/Flight-Delays-Cancellations/")

# Create initial DataFrame
result = pd.DataFrame({
    "coords": coords,
    "station_name": station_name,
    "elevation": elevation
})

# Filter and parse coordinates
coordinates = []
valid_indices = []
for idx, item in enumerate(result["coords"]):
    coord = parse_coord(str(item))  # Ensure item is a string for parsing
    if coord is not None:
        coordinates.append(coord)
        valid_indices.append(idx)

# Filter result to keep only rows with valid coordinates
df_valid = result.iloc[valid_indices].reset_index(drop=True)

# Perform reverse geocoding on the valid coordinates
reverse_geocode = rg.search(coordinates)

# Extract geocode results
latitude = [i["lat"] for i in reverse_geocode]
longitude = [i["lon"] for i in reverse_geocode]
names = [i["name"] for i in reverse_geocode]
admin1 = [i["admin1"] for i in reverse_geocode]
admin2 = [i["admin2"] for i in reverse_geocode]
countries = [i["cc"] for i in reverse_geocode]

# Create the final DataFrame with geocoded information
result_df = pd.DataFrame({
    "station_name": df_valid["station_name"].values,
    "coords": df_valid["coords"].values,
    "elevation": df_valid["elevation"].values,
    "latitude": latitude,
    "longitude": longitude,
    "names": names,
    "admin1": admin1,
    "admin2": admin2,
    "country": countries
})

# Save result to CSV
print("Saving result.")
result_df.to_csv("ncei-lcd-list_new.csv", index=False)
print("Completed metadata extraction.")
