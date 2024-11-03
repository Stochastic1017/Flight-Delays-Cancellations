
import pandas as pd
import os

# Define columns to drop as specified
columns_to_drop = [
    # Redundant Datetime columns
    "Year", "Quarter", "Month", "DayofMonth",
    
    # Redundant Airline Info columns
    "Operated_or_Branded_Code_Share_Partners", "DOT_ID_Marketing_Airline",
    "DOT_ID_Operating_Airline", "Flight_Number_Marketing_Airline",
    "IATA_Code_Marketing_Airline", "Originally_Scheduled_Code_Share_Airline",
    "DOT_ID_Originally_Scheduled_Code_Share_Airline",
    "IATA_Code_Originally_Scheduled_Code_Share_Airline",
    "IATA_Code_Operating_Airline", "Flight_Num_Originally_Scheduled_Code_Share_Airline",
    "Tail_Number",
    
    # Redundant Origin Info columns
    "Origin", "OriginAirportSeqID", "OriginCityMarketID", "OriginStateFips",
    "OriginState", "OriginWac", "OriginStateName",
    
    # Redundant Destination Info columns
    "Dest", "DestAirportSeqID", "DestCityMarketID", "DestStateFips",
    "DestState", "DestWac", "DestStateName",
    
    # Redundant Departure Time Info columns
    "CRSDepTime", "DepDelay", "DepDelayMinutes", "DepartureDelayGroups",
    "DepTimeBlk", "DepDel15", "TaxiOut",
    
    # Redundant Arrival Time Info columns
    "CRSArrTime", "ArrDelay", "ArrDelayMinutes", "ArrivalDelayGroups",
    "ArrTimeBlk", "WheelsOn", "ArrDel15",
    
    # Redundant Cancellation Info columns
    "Diverted", "CancellationCode", "Duplicate", "AirTime", "Flights", "DistanceGroup",
    
    # Delay columns
    'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay',
    
    # Redundant Gate Return Info column
    "LongestAddGTime"
]

# Define the base directory containing the year_month CSV files
base_dir = 'airport-data'
output_dir = 'airport_merged'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Dictionary to hold DataFrame per OriginAirportID
airport_data_dict = {}

# Iterate over each CSV file in the base directory
for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.csv'):
            # Construct full file path
            file_path = os.path.join(root, file)
            
            # Load the CSV
            print(f"Processing {file_path}")
            df = pd.read_csv(file_path, low_memory=False)
            
            # Drop the specified columns if they exist in the DataFrame
            df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
            df = df.iloc[:, :-48]
            
            # Iterate through unique OriginAirportID values in the current DataFrame
            for origin_id in df['OriginAirportID'].unique():
                # Filter the subset of data for the current OriginAirportID
                subset = df[df['OriginAirportID'] == origin_id]
                
                # Check if this OriginAirportID already has data in the dictionary
                if origin_id in airport_data_dict:
                    # Append new data to the existing DataFrame
                    airport_data_dict[origin_id] = pd.concat([airport_data_dict[origin_id], subset], ignore_index=True)
                else:
                    # Create a new entry for this OriginAirportID
                    airport_data_dict[origin_id] = subset

# Save each OriginAirportID DataFrame to a separate CSV file
for origin_id, data in airport_data_dict.items():
    filename = f"{origin_id}.csv"
    filepath = os.path.join(output_dir, filename)
    data.to_csv(filepath, index=False)
    print(f"Saved {filepath}")

print("Splitting and merging complete. All CSV files saved.")
