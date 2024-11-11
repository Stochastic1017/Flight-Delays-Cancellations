
import pickle
import pandas as pd
from dash import html, Output, Input, State, callback
import gcsfs
from .prediction_helpers import (haversine, get_weather_data_for_prediction, 
                                 get_weather_estimates, convert_to_utc, 
                                 validate_time_format)

# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Initialize Google Cloud Storage
fs = gcsfs.GCSFileSystem(project='Flights-Weather-Project', token='flights-weather-project-f94d306bee1f.json')

# Load airport metadata and closest station data
df_airport_metadata = pd.read_csv("gs://airport-weather-data/airports-list-us.csv", storage_options={"token": "flights-weather-project-f94d306bee1f.json"})
closest_weather_airport = pd.read_csv("gs://airport-weather-data/closest_airport_weather.csv", storage_options={"token": "flights-weather-project-f94d306bee1f.json"})

weather_features = [
    'HourlyDryBulbTemperature', 'HourlyWindSpeed', 'HourlyWindDirection',
    'HourlyDewPointTemperature', 'HourlyRelativeHumidity', 'HourlyVisibility',
    'HourlyStationPressure', 'HourlyWetBulbTemperature', 'HourlySkyConditions'
]

@callback(
    Output("prediction-output", "children"),
    Output("airline-input", "style"),
    Output("origin-airport-input", "style"),
    Output("destination-airport-input", "style"),
    Output("date-input", "style"),
    Output("departure-time-input", "style"),
    Output("arrival-time-input", "style"),
    Input("predict-button", "n_clicks"),
    State("airline-input", "value"),
    State("origin-airport-input", "value"),
    State("destination-airport-input", "value"),
    State("departure-time-input", "value"),
    State("arrival-time-input", "value"),
    State("date-input", "date"),
)
def predict_flight_delay(n_clicks, airline, origin_airport, destination_airport, 
                         departure_time, arrival_time, date):
    if not n_clicks:
        return "", {}, {}, {}, {}, {}, {}

    # Check for required inputs and validate them
    errors = {}
    required_inputs = {
        "airline-input": airline,
        "origin-airport-input": origin_airport,
        "destination-airport-input": destination_airport,
        "date-input": date,
        "departure-time-input": departure_time,
        "arrival-time-input": arrival_time
    }
    
    for input_id, value in required_inputs.items():
        if not value:
            errors[input_id] = {"border": "2px solid red"}

    # Validate time format for departure and arrival times
    if departure_time and not validate_time_format(departure_time):
        errors["departure-time-input"] = {"border": "2px solid red"}
    
    if arrival_time and not validate_time_format(arrival_time):
        errors["arrival-time-input"] = {"border": "2px solid red"}

    if errors:
        return "Please fill all fields correctly.", errors.get("airline-input", {}), errors.get("origin-airport-input", {}), \
               errors.get("destination-airport-input", {}), errors.get("date-input", {}), \
               errors.get("departure-time-input", {}), errors.get("arrival-time-input", {})

    # Get airport coordinates and calculate distance
    origin_data = df_airport_metadata[df_airport_metadata['AIRPORT_ID'] == origin_airport].iloc[0]
    dest_data = df_airport_metadata[df_airport_metadata['AIRPORT_ID'] == destination_airport].iloc[0]
    origin_latitude, origin_longitude = origin_data['LATITUDE'], origin_data['LONGITUDE']
    dest_latitude, dest_longitude = dest_data['LATITUDE'], dest_data['LONGITUDE']
    distance = haversine(origin_latitude, origin_longitude, dest_latitude, dest_longitude)

    # Convert times to UTC
    departure_time_utc = convert_to_utc(departure_time, date, origin_latitude, origin_longitude)
    arrival_time_utc = convert_to_utc(arrival_time, date, dest_latitude, dest_longitude)
    
    # Retrieve weather forecasts (try api, else estimate using closest weather stations)
    try:
        weather_forecasts = get_weather_data_for_prediction(latitude=origin_latitude, longitude=origin_longitude, 
                                                            timestamp=departure_time_utc, username="uwm_li_xiangchen", 
                                                            password="YQIl6mz793")
    except Exception as api_error:
        print(f"API call failed with error: {api_error}. Using nearest station estimates instead.")
        weather_forecasts = get_weather_estimates(origin_airport_id=origin_airport, 
                                                departure_time=departure_time_utc,
                                                closest_weather_airport=closest_weather_airport,
                                                max_distance=100, n_nearest=5)

    # Prepare features for the model
    features = {
        "DayOfWeek": departure_time_utc.weekday(),
        "Marketing_Airline_Network": airline,
        "OriginAirportID": origin_airport,
        "DestAirportID": destination_airport,
        "Distance": distance,
        "CRSDepHour": departure_time_utc.hour,
        "CRSArrHour": arrival_time_utc.hour,
        "CRSDepMonth": departure_time_utc.month,
        "CRSDepDayOfWeek": departure_time_utc.weekday(),
        **{feature: weather_forecasts.get(feature, 0) for feature in weather_features}  # Default to 0 if missing
    }

    # Convert features to DataFrame
    feature_df = pd.DataFrame([features])

    # Encode categorical features to match training
    feature_df['Marketing_Airline_Network'] = feature_df['Marketing_Airline_Network'].astype('category').cat.codes
    feature_df['OriginAirportID'] = feature_df['OriginAirportID'].astype('category').cat.codes
    feature_df['DestAirportID'] = feature_df['DestAirportID'].astype('category').cat.codes

    # Ensure all columns have correct data types
    feature_df = feature_df.astype({
        "DayOfWeek": "int",
        "Marketing_Airline_Network": "int",
        "OriginAirportID": "int",
        "DestAirportID": "int",
        "Distance": "float",
        "CRSDepHour": "int",
        "CRSArrHour": "int",
        "CRSDepMonth": "int",
        "CRSDepDayOfWeek": "int",
        # Add types for weather features
        "HourlyDryBulbTemperature": "float",
        "HourlyWindSpeed": "float",
        "HourlyWindDirection": "float",
        "HourlyDewPointTemperature": "float",
        "HourlyRelativeHumidity": "float",
        "HourlyVisibility": "float",
        "HourlyStationPressure": "float",
        "HourlyWetBulbTemperature": "float"
    })

    # Load models using Singleton pattern
    with fs.open("gs://airport-weather-data/models/best_lgbm_regressor.pkl", "rb") as f:
        delay_models = pickle.load(f)

    # Load models using Singleton pattern
    with fs.open("gs://airport-weather-data/models/best_lgbm_classifier.pkl", "rb") as f:
        cancel_model = pickle.load(f)

    # Drop 'HourlySkyConditions' if it exists in feature_df
    if 'HourlySkyConditions' in feature_df.columns:
        feature_df = feature_df.drop(columns=['HourlySkyConditions'])

    # Proceed with the prediction
    delay_prediction = delay_models.predict(feature_df)[0]
    delay_msg = f"TotalFlightDelay: {delay_prediction:.2f} minutes"

    # Predict cancellation
    cancel_prediction = cancel_model.predict(feature_df)[0]
    cancel_msg = "Yes" if cancel_prediction == 1 else "No"

    return html.Div([
        html.H4("Prediction Results:"),
        html.P(f"Delay: {delay_msg}"),
        html.P(f"Cancellation Likelihood: {cancel_msg}")
    ]), {}, {}, {}, {}, {}, {}