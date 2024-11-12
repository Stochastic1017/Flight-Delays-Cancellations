
import pandas as pd
import time
import threading
import pickle
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# Load your data
print("Reading input file...")
data = pd.read_csv("airport-weather-data.csv")

# Feature Engineering
print("Conducting feature engineering...")
data['CRSDepHour'] = pd.to_datetime(data['UTC_CRSDepTime']).dt.hour
data['CRSArrHour'] = pd.to_datetime(data['UTC_CRSArrTime']).dt.hour
data['CRSDepMonth'] = pd.to_datetime(data['UTC_CRSDepTime']).dt.month
data['CRSDepDayOfWeek'] = pd.to_datetime(data['UTC_CRSDepTime']).dt.dayofweek

# Encode categorical features
print("Encoding categorical features...")
data['Marketing_Airline_Network'] = data['Marketing_Airline_Network'].astype('category').cat.codes
data['OriginAirportID'] = data['OriginAirportID'].astype('category').cat.codes
data['DestAirportID'] = data['DestAirportID'].astype('category').cat.codes
data['HourlySkyConditions'] = data['HourlySkyConditions'].astype('category').cat.codes

# Handle missing values for weather features
weather_features = [
    'HourlyDryBulbTemperature', 'HourlyWindSpeed', 'HourlyWindDirection', 
    'HourlyDewPointTemperature', 'HourlyRelativeHumidity', 'HourlyVisibility', 
    'HourlyStationPressure', 'HourlyWetBulbTemperature', 'HourlySkyConditions'
]

# Impute missing values and scale weather features
print("Imputing and standardizing features...")
imputer = SimpleImputer(strategy='mean')
scaler = StandardScaler()
data[weather_features] = imputer.fit_transform(data[weather_features])
data[weather_features] = scaler.fit_transform(data[weather_features])

# Prepare the feature set for model training
X = data[['DayOfWeek', 'Marketing_Airline_Network', 'OriginAirportID', 'DestAirportID', 'Distance', 
          'CRSDepHour', 'CRSArrHour', 'CRSDepMonth', 'CRSDepDayOfWeek'] + weather_features]

# Regression Task with Random Forest
y_delay = data[['ArrivalDelay', 'DepartureDelay', 'TotalFlightDelay', 'TaxiDelay']].fillna(0)

# Split dataset for delay predictions
X_train_delay, X_test_delay, y_train_delay, y_test_delay = train_test_split(X, y_delay, test_size=0.2, random_state=42)

# Define Random Forest hyperparameter grid
rf_param_grid = {
    'n_estimators': [50, 100],
    'max_depth': [10, 20, None],
    'max_features': ['auto', 'sqrt'],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'bootstrap': [True, False]
}

# Start timer function in a separate thread
def print_elapsed_time():
    start_time = time.time()
    while not stop_event.is_set():
        time.sleep(300)  # Wait for 5 minutes
        elapsed_time = time.time() - start_time
        print(f"Total time elapsed so far: {elapsed_time / 60:.2f} minutes")

# Set up a stop event and start the timer thread
stop_event = threading.Event()
timer_thread = threading.Thread(target=print_elapsed_time)
timer_thread.start()

# Initialize RandomForestRegressor with hyperparameter tuning
rf_regressor = RandomForestRegressor(random_state=42)

# Set up RandomizedSearchCV
grid_search_regressor = RandomizedSearchCV(
    estimator=rf_regressor, 
    param_distributions=rf_param_grid,
    n_iter=10,
    cv=3, 
    verbose=1, 
    random_state=42,
    n_jobs=-1
)

# Fit model with hyperparameter tuning for regression
print("Fitting regression model with hyperparameter tuning...")
grid_search_regressor.fit(X_train_delay, y_train_delay)

# Stop the timer thread after fitting is complete
stop_event.set()
timer_thread.join()

# Best model from grid search
best_rf_regressor = grid_search_regressor.best_estimator_

# Predict and evaluate delay model for each type of delay
print("Evaluating delay predictions:")
y_pred_delay = best_rf_regressor.predict(X_test_delay)
delay_types = ['ArrivalDelay', 'DepartureDelay', 'TotalFlightDelay', 'TaxiDelay']

for i, delay_type in enumerate(delay_types):
    mse = mean_squared_error(y_test_delay.iloc[:, i], y_pred_delay[:, i])
    print(f"Root Mean Squared Error (RMSE) for {delay_type}: {mse**(1/2)}")

# Save the regression model
with open("best_rf_regressor.pkl", "wb") as file:
    pickle.dump(best_rf_regressor, file)
print("Regression model saved as best_rf_regressor.pkl")

# Classification Task with Random Forest
y_cancel = data['Cancelled'].fillna(0).astype(int)
X_train_cancel, X_test_cancel, y_train_cancel, y_test_cancel = train_test_split(X, y_cancel, test_size=0.2, random_state=42)

# Initialize RandomForestClassifier and fit model for cancellation prediction
print("Fitting classifier model...")
classifier = RandomForestClassifier(n_estimators=100, random_state=42)
classifier.fit(X_train_cancel, y_train_cancel)

# Predict and evaluate cancellation model
y_pred_cancel = classifier.predict(X_test_cancel)
accuracy_cancel = accuracy_score(y_test_cancel, y_pred_cancel)
print(f"Accuracy for Cancellation Prediction: {accuracy_cancel}")

# Save the classification model
with open("random_forest_classifier.pkl", "wb") as file:
    pickle.dump(classifier, file)
print("Classification model saved as random_forest_classifier.pkl")
