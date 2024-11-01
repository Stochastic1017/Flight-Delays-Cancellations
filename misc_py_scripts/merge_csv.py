
import os
import pandas as pd

def merge_csv_files_in_chunks(input_folder, output_file, chunk_size=10000):
    # Remove the output file if it exists to start fresh
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Track if headers have been written to avoid duplicating them
    headers_written = False

    # Get a list of all CSV files in the input folder
    csv_files = [file for file in os.listdir(input_folder) if file.endswith('.csv')]
    total_files = len(csv_files)

    # Loop through all CSV files in the folder
    for i, file in enumerate(csv_files, start=1):
        file_path = os.path.join(input_folder, file)
        print(f"Processing file: {file_path} ({total_files - i} files left)")

        # Read and write in chunks
        for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
            # Write headers only once
            if not headers_written:
                chunk.to_csv(output_file, index=False, mode='w')
                headers_written = True
            else:
                chunk.to_csv(output_file, index=False, mode='a', header=False)

    print(f"All files merged into {output_file}")

# Usage
input_folder = '/home/stochastic1017/Documents/Flight-Delays-Cancellations/holiday_data'  # Replace with the path to your folder
output_file = '/home/stochastic1017/Documents/Flight-Delays-Cancellations/holiday_data.csv'  # Replace with the path and name of the output file

merge_csv_files_in_chunks(input_folder, output_file)
