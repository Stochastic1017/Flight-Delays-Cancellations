
import os
import pandas as pd
from glob import glob

airport_df = pd.read_csv("airports-list-us.csv")
airport_ids = list(airport_df["AIRPORT_ID"])

os.chdir("/home/stochastic1017/Documents/Flight-Delays-Cancellations/airport_merged")

files = [file_name.strip(".csv") for file_name in glob("*.csv")]

removed_rows = []
for id in airport_ids:
    if str(id) in files:
        print("retaining row with airport id:", str(id))
    else:
        print("retaining row with airport id:", str(id))
        removed_rows.append(str(id))

os.chdir("/home/stochastic1017/Documents/Flight-Delays-Cancellations/")

# Remove rows from airport_df where AIRPORT_ID is in removed_rows
airport_df = airport_df[~airport_df["AIRPORT_ID"].astype(str).isin(removed_rows)]

# Save the updated DataFrame to a new CSV if needed
airport_df.to_csv("filtered_airports-list-us.csv", index=False)

