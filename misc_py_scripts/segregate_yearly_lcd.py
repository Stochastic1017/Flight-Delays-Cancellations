
import os
import sys
import pandas as pd
from glob import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Check if year is provided as a command-line argument
if len(sys.argv) < 2:
    print("Usage: python segregate_yearly_lcd.py <year>")
    sys.exit(1)

# Get year from command-line argument
year = sys.argv[1]

# Read the CSV file to get only U.S. stations for the specified year
us_stations = set(pd.read_csv(f"ncei-lcd-list-{year}.csv")["station"])

# Define the main directory and change to the year-specific directory
main_dir = os.getcwd()
os.chdir(f"{main_dir}/{year}")

# List CSV files in the directory
files = glob("*.csv")

# Function to process each file and delete non-U.S. station files
def process_file(file):
    try:
        if file.strip(".csv") not in us_stations:
            os.remove(file)  # Deletes the file
            return f"Deleted {file}"
        else:
            return f"Kept {file}"
    except Exception as e:
        return f"Error processing {file}: {e}"

# Run the file processing in parallel with a progress bar
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_file = {executor.submit(process_file, file): file for file in files}
    for future in tqdm(as_completed(future_to_file), total=len(files), desc="Processing Files"):
        result = future.result()
        print(result)  # Prints whether the file was kept or deleted

# Change back to the main directory
os.chdir(main_dir)
