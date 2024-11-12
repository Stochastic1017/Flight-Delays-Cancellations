
import pandas as pd
import numpy as np
import time
import pickle
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.impute import SimpleImputer
from joblib import Parallel, delayed
import multiprocessing
from tqdm import tqdm  # For progress bar

# Set number of cores for parallel processing
N_CORES = multiprocessing.cpu_count()
print("Number of cores available for processing:", N_CORES)

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} completed in {time.time() - start_time:.2f} seconds")
        return result
    return wrapper

@timer_decorator
def process_datetime_chunk(chunk):
    """Process a chunk of datetime data"""
    return pd.DataFrame({
        'CRSDepHour': pd.to_datetime(chunk['UTC_CRSDepTime']).dt.hour,
        'CRSArrHour': pd.to_datetime(chunk['UTC_CRSArrTime']).dt.hour,
        'CRSDepMonth': pd.to_datetime(chunk['UTC_CRSDepTime']).dt.month,
        'CRSDepDayOfWeek': pd.to_datetime(chunk['UTC_CRSDepTime']).dt.dayofweek
    })

@timer_decorator
def parallel_feature_engineering(data):
    # Split data into chunks for parallel processing
    chunk_size = len(data) // N_CORES
    chunks = [data.iloc[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    print("Processing datetime features in parallel...")
    results = Parallel(n_jobs=N_CORES)(
        delayed(process_datetime_chunk)(chunk) for chunk in tqdm(chunks, desc="Datetime Feature Processing")
    )
    
    # Combine results and reset index to avoid duplicate labels
    combined_results = pd.concat(results).reset_index(drop=True)
    
    # Ensure alignment of indices before assignment
    data = data.reset_index(drop=True)
    
    # Update original dataframe
    for col in ['CRSDepHour', 'CRSArrHour', 'CRSDepMonth', 'CRSDepDayOfWeek']:
        data[col] = combined_results[col]
    
    return data

@timer_decorator
def process_weather_chunk(chunk, weather_features, imputer, scaler):
    """Process a chunk of weather data"""
    chunk_weather = chunk[weather_features].copy()
    chunk_weather = imputer.transform(chunk_weather)
    chunk_weather = scaler.transform(chunk_weather)
    return pd.DataFrame(chunk_weather, columns=weather_features)

@timer_decorator
def parallel_weather_processing(data, weather_features):
    # Initialize transformers
    imputer = SimpleImputer(strategy='mean')
    scaler = StandardScaler()
    
    # Fit transformers on full dataset
    print("Fitting imputer and scaler on weather data...")
    imputer.fit(data[weather_features])
    scaler.fit(data[weather_features])
    
    # Split data into chunks
    chunk_size = len(data) // N_CORES
    chunks = [data.iloc[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    print("Processing weather data in parallel...")
    results = Parallel(n_jobs=N_CORES)(
        delayed(process_weather_chunk)(chunk, weather_features, imputer, scaler)
        for chunk in tqdm(chunks, desc="Weather Feature Processing")
    )
    
    # Combine results
    processed_weather = pd.concat(results).reset_index(drop=True)
    data[weather_features] = processed_weather
    
    return data

@timer_decorator
def process_interaction_chunk(chunk, poly):
    """Process a chunk for interaction terms"""
    interaction_terms = poly.transform(chunk)
    return pd.DataFrame(interaction_terms, columns=poly.get_feature_names_out())

@timer_decorator
def parallel_interaction_terms(data, weather_features):
    # Initialize PolynomialFeatures
    poly = PolynomialFeatures(interaction_only=True, include_bias=False)
    print("Fitting polynomial interaction terms...")
    poly.fit(data[weather_features])
    
    # Split data into chunks
    chunk_size = len(data) // N_CORES
    chunks = [data[weather_features].iloc[i:i + chunk_size] 
             for i in range(0, len(data), chunk_size)]
    
    print("Creating interaction terms in parallel...")
    results = Parallel(n_jobs=N_CORES)(
        delayed(process_interaction_chunk)(chunk, poly)
        for chunk in tqdm(chunks, desc="Interaction Term Processing")
    )
    
    # Combine results
    interaction_df = pd.concat(results).reset_index(drop=True)
    return pd.concat([data.reset_index(drop=True), interaction_df], axis=1)

@timer_decorator
def train_rf_regressor(X_train, y_train, n_trees):
    """Train a single random forest regressor"""
    print(f"Training Random Forest Regressor with {n_trees} trees...")
    rf = RandomForestRegressor(
        n_estimators=n_trees,
        random_state=42,
        max_depth=15,
        min_samples_split=10
    )
    rf.fit(X_train, y_train)
    return rf

@timer_decorator
def parallel_train_delay_model(X_train, y_train):
    """Train delay models in parallel"""
    # Split trees among cores
    trees_per_core = 100 // N_CORES
    
    # Train separate forests for each target in parallel
    delay_types = ['ArrivalDelay', 'DepartureDelay', 'TotalFlightDelay', 'TaxiDelay']
    
    print("Training delay models in parallel...")
    models = Parallel(n_jobs=N_CORES)(
        delayed(train_rf_regressor)(
            X_train, y_train[delay_type], trees_per_core
        )
        for delay_type in tqdm(delay_types, desc="Delay Model Training")
    )
    
    return dict(zip(delay_types, models))

def main():
    start_time = time.time()
    
    # Load data
    print("Loading data...")
    data = pd.read_csv("airport-weather-data.csv")
    print("Data loaded successfully.")
    
    # Convert categorical columns
    cat_columns = ['Marketing_Airline_Network', 'OriginAirportID', 
                   'DestAirportID', 'HourlySkyConditions']
    print("Converting categorical columns to numerical codes...")
    for col in cat_columns:
        data[col] = data[col].astype('category').cat.codes
    
    # Feature engineering
    print("Engineering features...")
    data = parallel_feature_engineering(data)
    
    # Define weather features
    weather_features = [
        'HourlyDryBulbTemperature', 'HourlyWindSpeed', 'HourlyWindDirection',
        'HourlyDewPointTemperature', 'HourlyRelativeHumidity', 'HourlyVisibility',
        'HourlyStationPressure', 'HourlyWetBulbTemperature', 'HourlySkyConditions'
    ]
    
    # Process weather features
    print("Processing weather features...")
    data = parallel_weather_processing(data, weather_features)
    
    # Create interaction terms
    print("Creating interaction terms...")
    data = parallel_interaction_terms(data, weather_features)
    
    # Prepare features and targets
    feature_columns = ['DayOfWeek', 'Marketing_Airline_Network', 'OriginAirportID',
                       'DestAirportID', 'Distance', 'CRSDepHour', 'CRSArrHour',
                       'CRSDepMonth', 'CRSDepDayOfWeek'] + weather_features
    
    X = data[feature_columns]
    y_delay = data[['ArrivalDelay', 'DepartureDelay', 'TotalFlightDelay', 'TaxiDelay']].fillna(0)
    y_cancel = data['Cancelled'].fillna(0).astype(int)
    
    # Split data
    print("Splitting data into training and testing sets...")
    X_train_delay, X_test_delay, y_train_delay, y_test_delay = train_test_split(
        X, y_delay, test_size=0.2, random_state=42
    )
    
    # Train delay models in parallel
    print("Training delay models...")
    delay_models = parallel_train_delay_model(X_train_delay, y_train_delay)
    
    # Train cancellation model
    print("Training cancellation model...")
    cancel_model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=N_CORES,
        max_depth=15,
        min_samples_split=10
    )
    cancel_model.fit(X_train_delay, y_cancel)
    print("Cancellation model trained.")
    
    # Save models
    print("Saving models...")
    with open("delay_models_rf.pkl", "wb") as f:
        pickle.dump(delay_models, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open("cancel_model_rf.pkl", "wb") as f:
        pickle.dump(cancel_model, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("Models saved successfully.")
    
    # Make predictions and calculate metrics
    print("\nCalculating metrics...")
    for delay_type, model in delay_models.items():
        y_pred = model.predict(X_test_delay)
        rmse = np.sqrt(mean_squared_error(y_test_delay[delay_type], y_pred))
        print(f"RMSE for {delay_type}: {rmse:.2f}")
    
    y_pred_cancel = cancel_model.predict(X_test_delay)
    accuracy_cancel = accuracy_score(y_cancel, y_pred_cancel)
    print(f"Cancellation Prediction Accuracy: {accuracy_cancel:.4f}")
    
    print(f"\nTotal runtime: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
