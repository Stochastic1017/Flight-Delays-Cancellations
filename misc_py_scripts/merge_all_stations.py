
import pandas as pd
import os

# Load data from each year
ncei_lcd_2018 = pd.read_csv("ncei-lcd-list-2018.csv")
ncei_lcd_2019 = pd.read_csv("ncei-lcd-list-2019.csv")
ncei_lcd_2020 = pd.read_csv("ncei-lcd-list-2020.csv")
ncei_lcd_2021 = pd.read_csv("ncei-lcd-list-2021.csv")
ncei_lcd_2022 = pd.read_csv("ncei-lcd-list-2022.csv")
ncei_lcd_2023 = pd.read_csv("ncei-lcd-list-2023.csv")
ncei_lcd_2024 = pd.read_csv("ncei-lcd-list-2024.csv")

# Initialize intersection with the first DataFrame
ncei_lcd_merged = ncei_lcd_2018

# Iteratively merge with each successive year
for df in [ncei_lcd_2019, ncei_lcd_2020, ncei_lcd_2021, ncei_lcd_2022, ncei_lcd_2023, ncei_lcd_2024]:
    ncei_lcd_merged = pd.merge(ncei_lcd_merged, df, on=list(ncei_lcd_merged.columns), how='inner')

# Display merged DataFrame
df = ncei_lcd_merged

# Load the main list of stations
df = pd.read_csv("ncei-lcd-list-us.csv")
stations = df["station"].unique()

# Prepare a folder to save the merged files
os.makedirs("merge", exist_ok=True)

# Specify the year directories
years = range(2018, 2025)

# Process each station
for i, station in enumerate(stations):
    print(f"Currently at: station={station}, {i} out of {len(stations)}")
    # Initialize an empty list to store DataFrames for each year
    station_dfs = []
    
    for year in years:
        print(f"Currently at: {year} out of {years[-1]}")
        file_path = f"{year}/{station}.csv"
        
        # Check if the station file exists for this year
        if os.path.exists(file_path):
            # Read and append the yearly data
            df_year = pd.read_csv(file_path, low_memory=False)
            station_dfs.append(df_year)

    # If data exists for the station across years, concatenate and save it
    if station_dfs:
        merged_df = pd.concat(station_dfs, ignore_index=True)
        merged_df.to_csv(f"merge/{station}.csv", index=False)
        print(f"Merged file saved for station: {station}")

print("All stations processed.")