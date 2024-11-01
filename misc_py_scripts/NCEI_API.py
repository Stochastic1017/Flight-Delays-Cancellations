
import calendar
from pathlib import Path
import concurrent.futures
import requests
import time
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        df = pd.json_normalize(data["results"])
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
        df = pd.json_normalize(data["results"])
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
    duplicate_count = 0

    while True:
        params["offset"] = offset
        attempts = 0

        while attempts < max_retries:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    current_batch = data["results"]

                    if current_batch == last_batch:
                        duplicate_count += 1
                    else:
                        duplicate_count = 0

                    all_data.extend(current_batch)
                    last_batch = current_batch
                    print(f"Fetched {len(current_batch)} records with offset {offset}")

                    if len(current_batch) < params["limit"] or duplicate_count >= 1:
                        break
                else:
                    print("No more data available.")
                    break

                offset += params["limit"]
                time.sleep(1)
                break 

            elif response.status_code == 503:
                attempts += 1
                wait_time = 2 ** attempts 
                print(f"503 Error: Service Unavailable. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

            else:
                print(f"Error: {response.status_code} - {response.text}")
                return

        if attempts == max_retries or (duplicate_count >= 1 and len(current_batch) < params["limit"]):
            print("Max retries reached or duplicate batch confirmed as last. Exiting.")
            break

    if all_data:
        df = pd.json_normalize(all_data)
        
        df.drop_duplicates(inplace=True)
        df.to_csv(f"{datasetid}_{location_type}.csv", index=False)
        print(f"Saved all data to {datasetid}_{location_type}.csv with {len(df)} records.")
    
    else:
        print("No data retrieved.")

def get_us_data_batch(datasetid, token, startdate, enddate, country_fips=None, state_fips=None, city_id=None, max_retries=5):
    start = time.time()
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    
    def build_query(param_name, items):
        return "&".join([f"{param_name}={item}" for item in items]) if items else ""
    
    params = {
        "datasetid": datasetid,
        "startdate": startdate,
        "enddate": enddate,
        "limit": 1000,
    }
    
    headers = {
        "token": token
    }
    
    all_data = []
    max_batch_size = 10
    last_batch = None
    duplicate_count = 0

    # Create batches if both state_fips and city_id are provided
    if state_fips is not None and city_id is not None:
        batches = [
            state_fips[i:i + max_batch_size] for i in range(0, len(state_fips), max_batch_size)
        ] + [
            city_id[i:i + max_batch_size] for i in range(0, len(city_id), max_batch_size)
        ]
    else:
        # Only include available location parameters if one or the other is missing
        batches = [state_fips[i:i + max_batch_size] for i in range(0, len(state_fips), max_batch_size)] if state_fips else []
        batches += [city_id[i:i + max_batch_size] for i in range(0, len(city_id), max_batch_size)] if city_id else []

    # Process each batch
    for batch in batches:
        offset = 0
        while True:
            country_query = build_query("locationid", country_fips)
            location_query = build_query("locationid", batch)
            full_query = f"{country_query}&{location_query}"

            params["offset"] = offset
            full_url = url + "?" + full_query
            
            attempts = 0
            while attempts < max_retries:
                try:
                    response = requests.get(full_url, headers=headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "results" in data:
                            current_batch = data["results"]

                            if current_batch == last_batch:
                                duplicate_count += 1
                                print("Duplicate batch detected. Stopping further requests.")
                                break
                            else:
                                duplicate_count = 0

                            all_data.extend(current_batch)
                            last_batch = current_batch 
                            print(f"Fetched {len(current_batch)} records with offset {offset}")

                            if len(current_batch) < params["limit"]:
                                break
                        
                        else:
                            print("No more data found.")
                            break
                        
                        offset += params["limit"]
                        time.sleep(1)
                        break

                    elif response.status_code == 500:
                        attempts += 1
                        wait_time = 2 ** attempts
                        print(f"500 Error: Retrying in {wait_time} seconds (attempt {attempts})...")
                        time.sleep(wait_time)
                        if attempts == max_retries:
                            print("Max retries reached for 500 Error. Skipping this batch.")
                            break

                    elif response.status_code == 503:
                        attempts += 1
                        wait_time = 2 ** attempts 
                        print(f"503 Error: Retrying in {wait_time} seconds (attempt {attempts})...")
                        time.sleep(wait_time)
                        if attempts == max_retries:
                            print("Max retries reached for 503 Error. Skipping this batch.")
                            break

                    else:
                        print(f"Error: {response.status_code} - {response.text}")
                        return

                except requests.exceptions.ReadTimeout:
                    attempts += 1
                    wait_time = 2 ** attempts 
                    print(f"Read timeout error: Retrying in {wait_time} seconds (attempt {attempts})...")
                    time.sleep(wait_time)
                    if attempts == max_retries:
                        print("Max retries reached for Read Timeout. Skipping this batch.")
                        break

            if attempts == max_retries or duplicate_count >= 1:
                print("Max retries reached or duplicate batch confirmed as last. Exiting.")
                break

        if duplicate_count >= 1:
            break

    # Save the data if retrieved
    if all_data:
        df = pd.json_normalize(all_data)
        df.drop_duplicates(inplace=True)
        
        print("Total unique records fetched:", len(df))
        df.to_csv(f"{datasetid}_{startdate}_{enddate}_US_data.csv", index=False)
        print(f"Saved data to {datasetid}_{startdate}_{enddate}_US_data.csv")
        print(f"Time Taken: {time.time() - start}")
    else:
        print("No data retrieved.")

def scrape_interval(datasetid, token, interval_start, interval_end, country_fips, state_fips, city_id):
    print(f"Scraping data from [{interval_start} <-> {interval_end}] using token: {token}")
    get_us_data_batch(
        datasetid=datasetid,
        token=token,
        startdate=interval_start,
        enddate=interval_end,
        country_fips=country_fips,
        state_fips=state_fips,
        city_id=city_id
    )

def parallel_scrape_month(datasetid, token, year, month, country_fips=None, state_fips=None, city_id=None, max_workers=3, delay_between_starts=0.2):
    start_date = datetime(year, month, 1)
    end_date = start_date.replace(day=28) + timedelta(days=4)
    end_date = end_date - timedelta(days=end_date.day - 1)

    intervals = []
    current_date = start_date
    while current_date < end_date:
        interval_start = current_date.strftime("%Y-%m-%d")
        interval_end = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
        intervals.append((interval_start, interval_end))
        current_date += timedelta(days=2)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for interval_start, interval_end in intervals:
            future = executor.submit(
                scrape_interval,
                datasetid,
                token,
                interval_start,
                interval_end,
                country_fips,
                state_fips,
                city_id
            )
            futures.append(future)
            time.sleep(delay_between_starts)

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in scraping interval: {e}")

def parallel_scrape_year(datasetid, tokens, year, months, country_fips=None, state_fips=None, city_id=None):
    
    if len(tokens) < len(months):
        raise ValueError("Number of tokens must be equal to or greater than the number of months to scrape.")

    with ThreadPoolExecutor(max_workers=len(tokens)) as executor:
        futures = []
        for i, month in enumerate(months):
            token = tokens[i % len(tokens)]
            future = executor.submit(
                parallel_scrape_month,
                datasetid,
                token,
                year,
                month,
                country_fips,
                state_fips,
                city_id,
                max_workers=3,
                delay_between_starts=0.5
            )
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in scraping month: {e}")

def find_missing(year, month):
    """
    Find missing two-day interval files for a given year and month.
    
    Args:
        year (int): The year to check
        month (int): The month to check
    
    Returns:
        list: List of missing file names
    """

    current_date = datetime(year, month, 1)
    next_month = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    
    expected_files = set()
    while current_date < next_month:
        
        if current_date.day == calendar.monthrange(year, month)[1]:
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
        else:
            end_date = min(current_date + timedelta(days=1), next_month - timedelta(days=1))
            
        filename = f"GHCND_{current_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}_US_data.csv"
        expected_files.add(filename)
        current_date += timedelta(days=2)
    
    month_name = calendar.month_name[month]
    directory = Path(f"{year}/GHCND/{month_name}")
    
    try:
        existing_files = {f.name for f in directory.glob("*.csv")}
    except FileNotFoundError:
        print(f"Directory {directory} not found!")
        return list(expected_files) 
    
    missing_files = expected_files - existing_files

    return sorted(missing_files)

def process_multiple_months(year, months):
    """
    Process multiple months in parallel to find missing files.
    
    Args:
        year (int): The year to check
        months (list): List of months to check
    
    Returns:
        dict: Dictionary with months as keys and lists of missing files as values
    """
    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(months)) as executor:
        # Create future to month mapping
        future_to_month = {
            executor.submit(find_missing, year, month): month 
            for month in months
        }
        
        for future in concurrent.futures.as_completed(future_to_month):
            month = future_to_month[future]
            try:
                missing_files = future.result()
                results[month] = missing_files
            except Exception as e:
                print(f"Error processing month {month} ({calendar.month_name[month]}): {e}")
                results[month] = []
    
    return results 

def extract_dates_from_filenames(filenames):
    """Extracts date intervals from filenames of the form GHCND_YYYY-MM-DD_YYYY-MM-DD_US_data.csv."""
    date_intervals = []
    for filename in filenames:
        parts = filename.split('_')
        if len(parts) >= 3:
            start_date = parts[1]
            end_date = parts[2]
            date_intervals.append((start_date, end_date))
    return date_intervals

datasetid = "PRECIP_15"
country_fips = ["FIPS:US"]

state_df = pd.read_csv(f"state_per_data/{datasetid}_ST.csv")
state_fips = list(state_df["id"])

city_df = pd.read_csv(f"city_per_data/{datasetid}_CITY.csv")
city_id = list(city_df[city_df["id"].str.contains("CITY:US")]["id"])

tokens = [
    "yQUJRypwhhqCeDvqpztgBbOSKNOEMXUg",
    "TsjPjsNnxMbJDXzcVwyMFhRTvZBGAiwo",
    "paRloOvWCtAUaWvPthxzWmcdHQfclDlP",
    "OOpfXMeTEAzUEXHDOXnQaKllfRRYCfYs",
    "fsPnjacYKYJuXJIWTSPXuQGUaSRXsTgU"
]

get_us_data_batch(datasetid=datasetid, token=tokens[0], startdate="2018-01-01", enddate="2018-12-31")