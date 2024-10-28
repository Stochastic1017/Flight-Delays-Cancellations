
import os
import glob
import pandas as pd
import shutil

def filter_us_stations(source_dir, us_stations_csv):
    # Save the current directory to return to it later
    original_dir = os.getcwd()

    # Load the CSV with US stations
    all_us_stations = pd.read_csv(us_stations_csv)
    us_station_ids = set(all_us_stations["Station ID"])

    # Set the path for the source directory (either GSOY or GSOM)
    os.chdir(source_dir)

    # Get all CSV files in the directory
    all_files = glob.glob("*.csv")

    # Check each filename (without ".csv") against US station IDs
    matching_stations = [item.strip(".csv") for item in all_files if item.strip(".csv") in us_station_ids]

    # Create the target directory name in the original directory (e.g., GSOY_US or GSOM_US)
    target_dir = os.path.join(original_dir, f"{source_dir}_US")
    os.makedirs(target_dir, exist_ok=True)

    # Copy matching files to the new directory in the original directory
    for station_id in matching_stations:
        file_name = f"{station_id}.csv"
        shutil.copy(file_name, os.path.join(target_dir, file_name))

    # Change back to the original directory
    os.chdir(original_dir)

    print(f"Files for US stations copied to {target_dir}")

filter_us_stations("GSOY", "ghcnd-stations-us.csv")
filter_us_stations("GSOM", "ghcnd-stations-us.csv")
