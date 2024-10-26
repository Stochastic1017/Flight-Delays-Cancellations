
import requests
import pandas as pd

def get_data_types(startdate="2018-01-01", enddate="2024-12-31"):

    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/datasets"
    
    params = {
        "startdate": startdate,
        "enddate": enddate
    }

    headers = {
    "token": "iQArVgwZRxeuLqISCQMUOMDjFXAXNsmb"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.json_normalize(data["results"])  # Adjust key based on JSON structure
        print(df)
        
        df.to_csv(f"NCEI_data_types.csv", index=False)
    
    else:
        print("Error:", response.status_code, response.text)

def get_location_types(datasetid, startdate="2018-01-01", enddate="2024-12-31"):

    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/locationcategories"

    params = {
        "datasetid": datasetid,
        "startdate": startdate,
        "enddate": enddate,
        "limit": 1000,
    }

    headers = {
    "token": "iQArVgwZRxeuLqISCQMUOMDjFXAXNsmb"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print(data)
        df = pd.json_normalize(data["results"])  # Adjust key based on JSON structure
        print("length of df:", len(df))
        
        df.to_csv(f"location_{datasetid}.csv", index=False)
    
    else:
        print("Error:", response.status_code, response.text)

def get_country(datasetid):
     
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/locations"

    params = {
        "datasetid": datasetid,
        "locationcategoryid": "CNTRY",
        "limit": 1000,
    }

    headers = {
        "token": "iQArVgwZRxeuLqISCQMUOMDjFXAXNsmb"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.json_normalize(data["results"])  # Adjust key based on JSON structure
        print("length of df:", len(df))
        print(df)
        
        df.to_csv(f"{datasetid}_CNTRY.csv", index=False)
    
    else:
        print("Error:", response.status_code, response.text)


def get_state(datasetid):
     
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/locations"

    params = {
        "datasetid": datasetid,
        "locationcategoryid": "ST",
        "limit": 1000,
    }

    headers = {
        "token": "iQArVgwZRxeuLqISCQMUOMDjFXAXNsmb"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.json_normalize(data["results"])  # Adjust key based on JSON structure
        print("length of df:", len(df))
        print(df)
        
        df.to_csv(f"{datasetid}_ST.csv", index=False)
    
    else:
        print("Error:", response.status_code, response.text)

def get_us_data(datasetid, startdate, enddate, state_fips, station_ids=None):
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"

    # Build location and station queries
    location_query = "&".join([f"locationid={loc}" for loc in state_fips])
    station_query = "&".join([f"stationid={stn}" for stn in station_ids]) if station_ids else ""
    
    params = {
        "datasetid": datasetid,
        "startdate": startdate,
        "enddate": enddate,
        "limit": 1000,
    }
    
    headers = {
        "token": "iQArVgwZRxeuLqISCQMUOMDjFXAXNsmb"
    }
    
    all_data = []
    offset = 0
    
    while True:
        params["offset"] = offset
        
        # Make the request with combined location and station query
        full_url = url + "?" + location_query
        if station_query:
            full_url += "&" + station_query
        
        response = requests.get(full_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if "results" in data:
                all_data.extend(data["results"])
                print(f"Fetched {len(data['results'])} records with offset {offset}")
                
                # Exit loop if fewer than limit results are returned
                if len(data["results"]) < params["limit"]:
                    break
            else:
                print("No more data found.")
                break
        else:
            print("Error:", response.status_code, response.text)
            break
        
        offset += params["limit"]

    # Convert to DataFrame
    if all_data:
        df = pd.json_normalize(all_data)
        print("Total records fetched:", len(df))
        print(df)
        
        # Uncomment to save as CSV
        df.to_csv(f"{datasetid}_{startdate}_{enddate}_data.csv", index=False)
    else:
        print("No data retrieved.")

# Main function to read FIPS CSV and loop over states
def process_states(csv_file, datasetid, startdate, enddate):
    # Read CSV with FIPS codes
    fips_data = pd.read_csv(csv_file)
    
    # Loop over each state row in the CSV
    for _, row in fips_data.iterrows():
        state_name = row['name']
        state_fips = row['id']
        
        print(f"Processing data for {state_name} ({state_fips})...")
        
        # Call get_us_data for each state
        get_us_data(datasetid, startdate, enddate, state_fips, state_name)

data_type = "GSOM"
process_states(
    csv_file=f"state_per_data/{data_type}_ST.csv",  # Path to your CSV file
    datasetid=f"{data_type}",
    startdate="2023-01-01",
    enddate="2023-12-31",
)
