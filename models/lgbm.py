import pandas as pd
import pickle
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import lightgbm as lgb

# Load your data
print("Reading input file...")
data = pd.read_csv("airport-weather-data.csv")
data = data.sample(frac=0.3, random_state=42)

# Conduct feature engineering
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

# Handle missing values for weather features
weather_features = [
    'HourlyDryBulbTemperature', 'HourlyWindSpeed', 'HourlyWindDirection', 
    'HourlyDewPointTemperature', 'HourlyRelativeHumidity', 'HourlyVisibility', 
    'HourlyStationPressure', 'HourlyWetBulbTemperature'
]

# Impute missing values and scale weather features
print("Imputing and standardizing features...")
imputer = SimpleImputer(strategy='mean')
scaler = StandardScaler()
data[weather_features] = imputer.fit_transform(data[weather_features])
data[weather_features] = scaler.fit_transform(data[weather_features])

# Prepare the feature set (18 features)
X = data[['DayOfWeek', 'Marketing_Airline_Network', 'OriginAirportID', 'DestAirportID', 'Distance', 
          'CRSDepHour', 'CRSArrHour', 'CRSDepMonth', 'CRSDepDayOfWeek'] + weather_features]

# Regression Task with LGBM for 'TotalFlightDelay'
y_delay = data['TotalFlightDelay'].fillna(0)  # Select one delay type for simplicity

# Split dataset for delay predictions
X_train_delay, X_test_delay, y_train_delay, y_test_delay = train_test_split(X, y_delay, test_size=0.2, random_state=42)

# Define hyperparameter grid for LGBM with optimized ranges for regression
lgbm_param_grid = {
    'num_leaves': [20, 30, 40],
    'max_depth': [5, 10, 15],
    'learning_rate': [0.05, 0.1, 0.15],
    'n_estimators': [150, 200, 250],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'reg_alpha': [0.1, 0.3, 0.5],  # L1 regularization
    'reg_lambda': [0.1, 0.3, 0.5]  # L2 regularization
}

# Initialize LGBMRegressor
lgbm_regressor = lgb.LGBMRegressor(random_state=42)

# Set up RandomizedSearchCV for hyperparameter tuning
print("Starting hyperparameter tuning for delay prediction...")
grid_search_lgbm = RandomizedSearchCV(
    estimator=lgbm_regressor, 
    param_distributions=lgbm_param_grid,
    n_iter=15,  # Adjust iterations for more exhaustive search if needed
    cv=5,  # More folds for better model robustness
    verbose=1, 
    random_state=42,
    n_jobs=2
)

# Fit model with hyperparameter tuning for regression
grid_search_lgbm.fit(X_train_delay, y_train_delay)

# Best model from grid search for regression
best_lgbm_regressor = grid_search_lgbm.best_estimator_

# Display the most important 18 features for delay prediction
print("Displaying the top 18 most important features for delay prediction:")
feature_importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': best_lgbm_regressor.feature_importances_
}).sort_values(by='Importance', ascending=False)
print(feature_importances.head(18))

# Predict and calculate RMSE for delay prediction
print("Evaluating delay prediction model...")
y_pred_delay = best_lgbm_regressor.predict(X_test_delay)
rmse = mean_squared_error(y_test_delay, y_pred_delay, squared=False)
print(f"Root Mean Squared Error (RMSE) for TotalFlightDelay: {rmse}")

# Save the regression model
with open("best_lgbm_regressor.pkl", "wb") as file:
    pickle.dump(best_lgbm_regressor, file)
print("LGBM regression model saved as best_lgbm_regressor.pkl")

# Classification Task with LGBM for 'Cancelled' feature
y_cancel = data['Cancelled']  # Target for classification

# Split dataset for cancellation predictions
X_train_cancel, X_test_cancel, y_train_cancel, y_test_cancel = train_test_split(X, y_cancel, test_size=0.2, random_state=42)

# Define hyperparameter grid for LGBM with optimized ranges for classification
lgbm_class_param_grid = {
    'num_leaves': [20, 30, 40],
    'max_depth': [5, 10, 15],
    'learning_rate': [0.05, 0.1, 0.15],
    'n_estimators': [150, 200, 250],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'reg_alpha': [0.1, 0.3, 0.5],  # L1 regularization
    'reg_lambda': [0.1, 0.3, 0.5]  # L2 regularization
}

# Initialize LGBMClassifier
lgbm_classifier = lgb.LGBMClassifier(random_state=42)

# Set up RandomizedSearchCV for hyperparameter tuning for classification
print("Starting hyperparameter tuning for cancellation prediction...")
grid_search_lgbm_class = RandomizedSearchCV(
    estimator=lgbm_classifier, 
    param_distributions=lgbm_class_param_grid,
    n_iter=15,  # Adjust iterations for more exhaustive search if needed
    cv=5,  # More folds for better model robustness
    verbose=1, 
    random_state=42,
    n_jobs=2
)

# Fit model with hyperparameter tuning for classification
grid_search_lgbm_class.fit(X_train_cancel, y_train_cancel)

# Best model from grid search for classification
best_lgbm_classifier = grid_search_lgbm_class.best_estimator_

# Display the most important 18 features for cancellation prediction
print("Displaying the top 18 most important features for cancellation prediction:")
feature_importances_class = pd.DataFrame({
    'Feature': X.columns,
    'Importance': best_lgbm_classifier.feature_importances_
}).sort_values(by='Importance', ascending=False)
print(feature_importances_class.head(18))

# Predict and calculate RMSE for delay prediction
print("Evaluating delay prediction model...")
y_pred_delay = best_lgbm_regressor.predict(X_test_delay)
rmse = mean_squared_error(y_test_delay, y_pred_delay, squared=False)
print(f"Root Mean Squared Error (RMSE) for TotalFlightDelay: {rmse}")

# Predict and calculate accuracy for cancellation classification
print("Evaluating cancellation prediction model...")
y_pred_cancel = best_lgbm_classifier.predict(X_test_cancel)
accuracy = accuracy_score(y_test_cancel, y_pred_cancel)
print(f"Accuracy for cancellation prediction: {accuracy:.2f}")

# Save the classification model
with open("best_lgbm_classifier.pkl", "wb") as file:
    pickle.dump(best_lgbm_classifier, file)
print("LGBM classification model saved as best_lgbm_classifier.pkl")
