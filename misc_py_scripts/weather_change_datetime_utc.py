
import pandas as pd
import pytz
from timezonefinder import TimezoneFinder
from glob import glob
import os

# Initialize TimezoneFinder
tf = TimezoneFinder()

# Function to convert timestamps to a unified time zone (e.g., UTC)
def convert_to_utc(df, datetime_col, lat_col, lon_col):
    print(f"Starting time zone conversion for column: {datetime_col}")
    df[datetime_col] = pd.to_datetime(df[datetime_col], errors='coerce')
    print(f"Converted {datetime_col} to datetime format")

    def local_to_utc(row):
        if pd.isnull(row[datetime_col]) or pd.isnull(row[lat_col]) or pd.isnull(row[lon_col]):
            print(f"Skipping row {row.name}: Missing datetime, latitude, or longitude")
            return None
        try:
            local_tz = tf.timezone_at(lng=row[lon_col], lat=row[lat_col])
            if local_tz is not None:
                local_time = row[datetime_col].replace(tzinfo=pytz.timezone(local_tz))
                utc_time = local_time.astimezone(pytz.utc)
                return utc_time
            else:
                print(f"Row {row.name}: Unable to find timezone")
                return None
        except Exception as e:
            print(f"Error converting row {row.name}: {e}")
            return None

    df['UTC_' + datetime_col] = df.apply(local_to_utc, axis=1)
    print(f"Completed time zone conversion for {datetime_col}")
    return df

# Paths to data directories
weather_data_path = 'ncei-lcd'

# Load metadata CSVs for latitude and longitude information
print("Loading metadata files...")
weather_meta = pd.read_csv('ncei-lcd-list-us.csv')
print("Weather metadata loaded successfully")

# Display metadata column names
print("Weather metadata columns:", weather_meta.columns)

# Process weather data files
print("Processing weather data files...")
for filepath in glob(os.path.join(weather_data_path, '*.csv')):
    filename = os.path.basename(filepath)
    station_id = filename.split('.')[0]  # Extract the station ID from the filename
    print(f"\nProcessing file: {filename} with station ID: {station_id}")
    
    # Check if the station ID exists in the metadata
    if station_id in weather_meta['station'].astype(str).values:
        print(f"Station ID {station_id} found in metadata")
        weather_data = pd.read_csv(filepath, low_memory=False)
        print(f"Loaded data file: {filename} with {len(weather_data)} rows")
        
        # Merge the weather data with its metadata
        metadata_row = weather_meta[weather_meta['station'].astype(str) == station_id]
        latitude = metadata_row['latitude'].values[0]
        longitude = metadata_row['longitude'].values[0]
        print(f"Metadata for station {station_id}: latitude = {latitude}, longitude = {longitude}")
        
        # Add latitude and longitude columns for time zone conversion
        weather_data['latitude'] = latitude
        weather_data['longitude'] = longitude
        print("Added latitude and longitude columns for time zone conversion")
        
        # Convert DATE column to UTC
        weather_data = convert_to_utc(weather_data, 'DATE', 'latitude', 'longitude')
        weather_data.drop(columns=['latitude', 'longitude'], inplace=True)
        print(f"Completed UTC conversion for {filename}")
        
        # Save the processed file with the original filename
        output_path = filepath  # Overwrite the original file
        weather_data.to_csv(output_path, index=False)
        print(f"Processed and saved {output_path}")
    else:
        print(f"Station ID {station_id} not found in metadata. Deleting {filename}.")
        os.remove(filepath)
        print(f"Deleted {filename}")

print("Time zone unification for all weather files complete.")
