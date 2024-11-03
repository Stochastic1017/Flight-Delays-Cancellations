
import os
import pandas as pd
from glob import glob
from collections import defaultdict

def calculate_nan_proportion(df, file_path):
    # Dictionary to store the proportion of NaN for each column
    nan_proportions = {}

    # Check if DataFrame is empty and delete if true
    if len(df) == 0:
        print(f"Empty DataFrame found and deleted: {file_path}")
        os.remove(file_path)  # Delete the empty file
        return nan_proportions  # Return empty dictionary if no rows are available

    # Loop through each column starting from the 10th column onward
    for col in df.columns[9:]:
        # Calculate the proportion of NaN values in the column
        nan_proportion = df[col].isna().sum() / len(df)
        nan_proportions[col] = nan_proportion

    return nan_proportions

# Dictionary to store feature names with less than 5% missing data and their counts
feature_counts = defaultdict(int)

# Loop through each year and files within each year
for year in range(2018, 2025):
    print("Currently at:", year)
    files = glob(f"{year}/*.csv")
    
    for i in range(1, len(files)):
        file_path = files[i]
        print(f"year: {year}. At {i} out of {len(files)-1}")
        
        df = pd.read_csv(file_path, low_memory=False)
        
        # Calculate NaN proportions for the current file, passing file_path for empty checks
        nan_proportions = calculate_nan_proportion(df, file_path)
        
        # Update count for each feature with <5% NaN
        for feature, nan_prop in nan_proportions.items():
            if pd.notna(nan_prop) and nan_prop < 0.05:  # Only consider if proportion is valid and <5%
                feature_counts[feature] += 1

# Convert feature counts to a sorted list for easy viewing
sorted_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)
print("Features with less than 5% missing data (sorted by frequency across files):")
for feature, count in sorted_features:
    print(f"{feature}: {count} files")
