
import pandas as pd
import numpy as np
import time
import pickle
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.impute import SimpleImputer

# Record start time
start_time = time.time()

# Load your data (ensure correct file path)
print("Starting data loading...")
data = pd.read_csv("airport-weather-data.csv")
print(f"Data loaded successfully: time={time.time() - start_time}")

# Feature Engineering
print("Starting Feature Engineering...")
data['CRSDepHour'] = pd.to_datetime(data['UTC_CRSDepTime']).dt.hour
data['CRSArrHour'] = pd.to_datetime(data['UTC_CRSArrTime']).dt.hour
data['CRSDepMonth'] = pd.to_datetime(data['UTC_CRSDepTime']).dt.month
data['CRSDepDayOfWeek'] = pd.to_datetime(data['UTC_CRSDepTime']).dt.dayofweek
print(f"Converted CRS times accordingly: time={time.time() - start_time}")

# Encode categorical features
categorical_features = ['Marketing_Airline_Network', 'OriginAirportID', 'DestAirportID']
for feature in categorical_features:
    data[feature] = data[feature].astype('category').cat.codes
print(f"Encoded categorical airplane features: time={time.time() - start_time}")

# Encode and add `HourlySkyConditions` to weather features
data['HourlySkyConditions'] = data['HourlySkyConditions'].astype('category').cat.codes
weather_features = [
    'HourlyDryBulbTemperature', 
    'HourlyWindSpeed', 
    'HourlyWindDirection', 
    'HourlyDewPointTemperature', 
    'HourlyRelativeHumidity', 
    'HourlyVisibility', 
    'HourlyStationPressure', 
    'HourlyWetBulbTemperature', 
    'HourlySkyConditions'
]
print(f"Encoded categorical weather feature (Hourly Sky Condition): time={time.time() - start_time}")

# Impute missing values and scale weather features
imputer = SimpleImputer(strategy='mean')
scaler = StandardScaler()
data[weather_features] = imputer.fit_transform(data[weather_features])
data[weather_features] = scaler.fit_transform(data[weather_features])
print(f"Imputed and Standardized values: time={time.time() - start_time}")

# Interaction terms between weather features, including `HourlySkyConditions`
poly = PolynomialFeatures(interaction_only=True, include_bias=False)
weather_interaction_terms = poly.fit_transform(data[weather_features])
interaction_df = pd.DataFrame(weather_interaction_terms, columns=poly.get_feature_names_out(weather_features))
data = pd.concat([data, interaction_df], axis=1)
print(f"Weather interaction terms added: time={time.time() - start_time}")

# Prepare the feature set
X = data[['DayOfWeek', 'Marketing_Airline_Network', 'OriginAirportID', 'DestAirportID', 'Distance', 
          'CRSDepHour', 'CRSArrHour', 'CRSDepMonth', 'CRSDepDayOfWeek'] + weather_features + list(interaction_df.columns)]

# Split dataset for multi-output delay predictions
y_delay = data[['ArrivalDelay', 'DepartureDelay', 'TotalFlightDelay', 'TaxiDelay']].fillna(0)
X_train_delay, X_test_delay, y_train_delay, y_test_delay = train_test_split(X, y_delay, test_size=0.2, random_state=42)

# Multi-output regression model for delay prediction using Random Forest
print(f"Starting multi-output random forest regressor: time={time.time() - start_time}")
multioutput_regressor = MultiOutputRegressor(RandomForestRegressor(n_estimators=100, random_state=42))
multioutput_regressor.fit(X_train_delay, y_train_delay)
print(f"Multi-output delay model trained with Random Forest: time={time.time() - start_time}")

# Save the delay model to a file
print(f"pickling multi-output random forest regressor: time={time.time() - start_time}")
with open("multioutput_regressor_rf.pkl", "wb") as f:
    pickle.dump(multioutput_regressor, f)
print(f"Successfully pickled model and as saved it as 'multioutput_regressor_rf.pkl' time:{time.time() - start_time}")

# Predict and evaluate delay model
y_pred_delay = multioutput_regressor.predict(X_test_delay)

# Calculate RMSE for each delay type individually
print("Reporting RMSE for each delay type...")
delay_types = ['ArrivalDelay', 'DepartureDelay', 'TotalFlightDelay', 'TaxiDelay']
rmse_values = {}
for i, delay in enumerate(delay_types):
    mse = mean_squared_error(y_test_delay.iloc[:, i], y_pred_delay[:, i])
    rmse = np.sqrt(mse)
    rmse_values[delay] = rmse
    print(f"RMSE for {delay}: {rmse}")


# Split dataset for cancellation predictions
print("Preparing data for cancellation classification...")
y_cancel = data['Cancelled'].fillna(0).astype(int)
X_train_cancel, X_test_cancel, y_train_cancel, y_test_cancel = train_test_split(X, y_cancel, test_size=0.2, random_state=42)

# Random Forest model for cancellation prediction
print(f"Starting binary random forest classifier: time={time.time() - start_time}")
classifier_rf = RandomForestClassifier(n_estimators=100, random_state=42)
classifier_rf.fit(X_train_cancel, y_train_cancel)
print(f"Cancellation model trained with Random Forest: time={time.time() - start_time}")

# Save the cancellation model to a file
print(f"pickling binary random forest classifier: time={time.time() - start_time}")
with open("classifier_rf.pkl", "wb") as f:
    pickle.dump(classifier_rf, f)
print(f"Cancellation model saved as 'classifier_rf.pkl' : time={time.time() - start_time}")

# Predict and evaluate cancellation model
y_pred_cancel = classifier_rf.predict(X_test_cancel)
accuracy_cancel = accuracy_score(y_test_cancel, y_pred_cancel)
print(f"Accuracy for Cancellation Prediction: {accuracy_cancel}")

# Record end time and print runtime
end_time = time.time()
print("\n")
print("-----------------------------------------------------")
print(f"Total runtime: {end_time - start_time:.2f} seconds")
print("-----------------------------------------------------")
print("\n")
