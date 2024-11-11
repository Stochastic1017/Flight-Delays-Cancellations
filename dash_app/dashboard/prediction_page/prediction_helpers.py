
import re
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder

# Function to calculate Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def convert_pressure_to_inhg(hpa):
    return hpa * 0.02953

def convert_visibility_to_miles(nmi):
    miles = nmi * 1.15078
    return min(miles, 10)  # Cap visibility at 10 miles

def get_weather_data_for_prediction(latitude, longitude, timestamp, username, password):
    # Define required continuous parameters with model-compatible names
    parameter_mapping = {
        "t_2m:C": "DryBulbTemperature",                   # Dry bulb temperature
        "wind_speed_10m:kmh": "WindSpeed",                # Wind speed
        "wind_dir_10m:d": "WindDirection",                # Wind direction
        "dew_point_2m:C": "DewPointTemperature",          # Dew point temperature
        "relative_humidity_2m:p": "RelativeHumidity",     # Relative humidity
        "visibility:nmi": "Visibility",                   # Visibility in miles
        "msl_pressure:hPa": "StationPressure",            # Station pressure in inHg
    }
    
    # Split timestamp into date and time, remove timezone
    timestamp_date = timestamp.strftime("%Y-%m-%d")
    timestamp_time = timestamp.strftime("%H:%M:%S")
    timestamp_str = f"{timestamp_date}T{timestamp_time}Z"  # Format as ISO 8601 without whitespace
    
    parameter_str = ",".join(parameter_mapping.keys())
    url = f"https://api.meteomatics.com/{timestamp_str}/{parameter_str}/{latitude},{longitude}/json?source=ecmwf-ifs"
    
    response = requests.get(url, auth=HTTPBasicAuth(username, password))
    
    if response.status_code == 200:
        data = response.json()
        
        # Initialize dictionary to store model-compatible weather data
        weather_data = {model_name: None for model_name in parameter_mapping.values()}

        for forecast in data.get("data", []):
            parameter = forecast.get("parameter")
            model_name = parameter_mapping.get(parameter)
            coordinates_data = forecast.get("coordinates", [{}])[0]
            dates = coordinates_data.get("dates", [])
            
            if model_name and dates:
                value = dates[0].get("value")
                if parameter == "msl_pressure:hPa":
                    weather_data[model_name] = convert_pressure_to_inhg(value)
                elif parameter == "visibility:nmi":
                    weather_data[model_name] = convert_visibility_to_miles(value)
                else:
                    weather_data[model_name] = value
            elif not model_name:
                print(f"Warning: Unexpected parameter '{parameter}' received from API and will be ignored.")
        
        return weather_data

    else:
        print("Request failed, status code:", response.status_code)
        print("Response content:", response.text)
        return None

def get_weather_estimates(origin_airport_id, departure_time, closest_weather_airport, 
                          max_distance=100, n_nearest=5):
    # Filter for the nearest weather stations to the origin airport
    nearest_stations = closest_weather_airport[
        closest_weather_airport['AIRPORT_ID'] == int(origin_airport_id)
    ]
    
    if nearest_stations.empty:
        print(f"No nearby stations found for airport {origin_airport_id}. Skipping.")
        return None

    # Limit to stations within max_distance, or use the closest n_nearest if none are within max_distance
    if nearest_stations[nearest_stations['DISTANCE_KM'] <= max_distance].empty:
        nearest_stations = nearest_stations.nsmallest(n_nearest, 'DISTANCE_KM')
    else:
        nearest_stations = nearest_stations[nearest_stations['DISTANCE_KM'] <= max_distance].head(n_nearest)
    
    # Define the weather features to retrieve
    features = [
        'HourlyDryBulbTemperature', 'HourlyWindSpeed', 'HourlyWindDirection',
        'HourlyDewPointTemperature', 'HourlyRelativeHumidity',
        'HourlyVisibility', 'HourlyStationPressure', 'HourlyWetBulbTemperature'
    ]
    
    # Initialize accumulators for averaging
    weather_sums = {feature: 0.0 for feature in features}
    valid_counts = {feature: 0 for feature in features}
    
    # Format departure time to YYYY-MM-DD for filtering date in the CSVs
    date_str = departure_time.strftime("%Y-%m-%d")
    
    # Load and process each nearest weather station file
    for _, station in nearest_stations.iterrows():
        station_id = int(station['STATION_ID'])
        file_path = f'gs://airport-weather-data/ncei-lcd/{station_id}.csv'
        
        try:
            # Load weather data for the station
            weather_df = pd.read_csv(file_path, storage_options={"token": "flights-weather-project-f94d306bee1f.json"})
            
            # Filter for the relevant date and find the closest time to the departure time
            weather_df['UTC_DATE'] = pd.to_datetime(weather_df['UTC_DATE'])
            daily_weather = weather_df[weather_df['UTC_DATE'].dt.date == departure_time.date()]
            
            if daily_weather.empty:
                print(f"No weather data found for station {station_id} on {date_str}.")
                continue
            
            # Find the closest time record to the departure time
            closest_time_idx = (daily_weather['UTC_DATE'] - departure_time).abs().idxmin()
            closest_weather = daily_weather.loc[closest_time_idx]
            
            # Accumulate feature values
            for feature in features:
                value = closest_weather.get(feature)
                if pd.notnull(value):
                    weather_sums[feature] += value
                    valid_counts[feature] += 1

        except FileNotFoundError:
            print(f"Weather file for station {station_id} not found.")
            continue

    # Calculate averages for each feature
    weather_averages = {}
    for feature in features:
        if valid_counts[feature] > 0:
            weather_averages[feature] = weather_sums[feature] / valid_counts[feature]
        else:
            weather_averages[feature] = None  # Handle missing data if no values were accumulated

    return weather_averages

# Function to convert local time to UTC
def convert_to_utc(local_time_str, date_str, lat, lon):
    tf = TimezoneFinder()
    local_time_zone = tf.timezone_at(lat=lat, lng=lon)
    local_time = datetime.strptime(f"{date_str} {local_time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(local_time_zone)
    local_dt = local_tz.localize(local_time)
    return local_dt.astimezone(pytz.UTC)

def validate_time_format(time_str):
    return bool(re.match(r'^[0-2]?\d:[0-5]\d$', time_str))
