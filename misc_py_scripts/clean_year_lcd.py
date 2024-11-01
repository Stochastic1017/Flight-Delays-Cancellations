
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

# Define the main directory and change to the year-specific directory
main_dir = os.getcwd()
os.chdir(f"{main_dir}/{year}")

# List CSV files in the directory
files = glob("*.csv")

# Function to process each file and replace it with filtered data
def process_file(file):
    try:
        # Read the CSV file
        df = pd.read_csv(file, low_memory=False)
        # Convert 'DATE' column to datetime format
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        # Filter for January, November, and December
        filtered_df = df[df['DATE'].dt.month.isin([1, 11, 12])]

        # Save the filtered data back to the original file
        filtered_df.to_csv(file, index=False)

    except Exception as e:
        print(f"Error processing {file}: {e}")

# Run the file processing in parallel with a progress bar
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_file = {executor.submit(process_file, file): file for file in files}
    for future in tqdm(as_completed(future_to_file), total=len(files), desc="Processing Files"):
        future.result()  # Ensure completion and catch any exceptions

# Change back to the main directory
os.chdir(main_dir)
