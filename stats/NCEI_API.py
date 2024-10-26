
import requests
import time
import pandas as pd

def get_data_types(token, startdate="2018-01-01", enddate="2024-12-31"):

    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/datasets"
    
    params = {
        "startdate": startdate,
        "enddate": enddate
    }

    headers = {
    "token": token}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.json_normalize(data["results"])  # Adjust key based on JSON structure
        print(df)
        
        df.to_csv(f"NCEI_data_types.csv", index=False)
    
    else:
        print("Error:", response.status_code, response.text)

def get_location_types(datasetid, token, startdate="2018-01-01", enddate="2024-12-31"):

    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/locationcategories"

    params = {
        "datasetid": datasetid,
        "startdate": startdate,
        "enddate": enddate,
        "limit": 1000,
    }

    headers = {
    "token": token}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print(data)
        df = pd.json_normalize(data["results"])  # Adjust key based on JSON structure
        print("length of df:", len(df))
        
        df.to_csv(f"location_{datasetid}.csv", index=False)
    
    else:
        print("Error:", response.status_code, response.text)

def get_location_data(datasetid, token, location_type, max_retries=5):
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/locations"

    params = {
        "datasetid": datasetid,
        "locationcategoryid": location_type,
        "limit": 1000,
    }

    headers = {
        "token": token
    }

    all_data = []
    offset = 0
    last_batch = None
    duplicate_count = 0  # Track consecutive duplicates

    while True:
        params["offset"] = offset
        attempts = 0

        while attempts < max_retries:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    current_batch = data["results"]

                    # Check for duplicate batch and increment count if it matches last batch
                    if current_batch == last_batch:
                        duplicate_count += 1
                    else:
                        duplicate_count = 0  # Reset if it's a new batch

                    # Append current batch to all_data if it's unique
                    all_data.extend(current_batch)
                    last_batch = current_batch  # Update last batch to current
                    print(f"Fetched {len(current_batch)} records with offset {offset}")

                    # Stop if fewer results than limit, or duplicates found twice in a row
                    if len(current_batch) < params["limit"] or duplicate_count >= 1:
                        break
                else:
                    print("No more data available.")
                    break

                offset += params["limit"]
                time.sleep(1)  # Pause between requests
                break  # Exit retry loop if successful

            elif response.status_code == 503:
                attempts += 1
                wait_time = 2 ** attempts  # Exponential backoff
                print(f"503 Error: Service Unavailable. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

            else:
                print(f"Error: {response.status_code} - {response.text}")
                return

        if attempts == max_retries or (duplicate_count >= 1 and len(current_batch) < params["limit"]):
            print("Max retries reached or duplicate batch confirmed as last. Exiting.")
            break

    # Convert all_data to DataFrame and filter for US cities if needed
    if all_data:
        df = pd.json_normalize(all_data)
        
        # Save to CSV
        df.drop_duplicates(inplace=True)
        df.to_csv(f"{datasetid}_{location_type}.csv", index=False)
        print(f"Saved all data to {datasetid}_{location_type}.csv with {len(df)} records.")
    
    else:
        print("No data retrieved.")

def get_us_data(datasetid, token, startdate, enddate, state_fips=["FIPS:06", "FIPS:36"], station_ids=None):

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
        "token": token}
    
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
        print("\n")
        print(df)
        
        # Uncomment to save as CSV
        df.to_csv(f"{datasetid}_{startdate}_{enddate}_US_data.csv", index=False)
    else:
        print("No data retrieved.")

datasetid = "GSOM"
fip_ids = pd.read_csv(f"state_per_data/{datasetid}_ST.csv")['id']
