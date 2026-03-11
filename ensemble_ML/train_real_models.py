#!/usr/bin/env python3
"""
Train the REAL ML models from the previous group using the processed data
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neighbors import KNeighborsRegressor
import joblib
import os

def train_events_model(data_path):
    """Train KNN model for events prediction"""
    print("🔵 Training Events KNN Model...")
    
    # Load data
    df = pd.read_csv(data_path)
    print(f"Data shape: {df.shape}")
    
    # Filter to event days only (any event column = 1)
    event_columns = ['Fall Break', 'Family Weekend', 'Home Football Game', 
                    'Home Football Game (Homecoming)', 'Labor Day']
    events_data = df[df[event_columns].any(axis=1)].copy()
    print(f"Events data shape: {events_data.shape}")
    
    # Prepare features and target
    X = events_data.drop(columns=['Current Availability'])
    y = events_data['Current Availability']
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Grid Search for best parameters
    param_grid = {
        'n_neighbors': [3, 5, 7, 9, 11],
        'weights': ['uniform', 'distance'],
        'metric': ['euclidean', 'manhattan']
    }
    
    knn = KNeighborsRegressor()
    grid_search = GridSearchCV(knn, param_grid, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)
    
    print("Training events model...")
    grid_search.fit(X_train, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    
    # Evaluate
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Events Model Performance:")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE: {mae:.4f}")
    print(f"  R²: {r2:.4f}")
    print(f"  Best params: {grid_search.best_params_}")
    
    # Save model
    os.makedirs("events_model", exist_ok=True)
    joblib.dump(best_model, "events_model/best_events_knn.pkl")
    print("✅ Events model saved to events_model/best_events_knn.pkl")
    
    return best_model

def train_summer_model(data_path):
    """Train KNN model for summer prediction"""
    print("\n🟡 Training Summer KNN Model...")
    
    # Load data
    df = pd.read_csv(data_path)
    
    # Filter to summer months (June, July, August) - assuming month column exists
    summer_data = df[df['month'].isin([6, 7, 8])].copy()
    print(f"Summer data shape: {summer_data.shape}")
    
    if len(summer_data) == 0:
        print("⚠️ No summer data found, using all data for summer model")
        summer_data = df.copy()
    
    # Prepare features and target
    X = summer_data.drop(columns=['Current Availability'])
    y = summer_data['Current Availability']
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Grid Search
    param_grid = {
        'n_neighbors': [3, 5, 7, 9, 11],
        'weights': ['uniform', 'distance'],
        'metric': ['euclidean', 'manhattan']
    }
    
    knn = KNeighborsRegressor()
    grid_search = GridSearchCV(knn, param_grid, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)
    
    print("Training summer model...")
    grid_search.fit(X_train, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    
    # Evaluate
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Summer Model Performance:")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE: {mae:.4f}")
    print(f"  R²: {r2:.4f}")
    print(f"  Best params: {grid_search.best_params_}")
    
    # Save model
    os.makedirs("summer_model", exist_ok=True)
    joblib.dump(best_model, "summer_model/best_summer_knn.pkl")
    print("✅ Summer model saved to summer_model/best_summer_knn.pkl")
    
    return best_model

def train_school_model(data_path):
    """Train KNN model for school year prediction"""
    print("\n🟢 Training School Year KNN Model...")
    
    # Load data
    df = pd.read_csv(data_path)
    
    # Filter to school year months (excluding summer)
    school_data = df[~df['month'].isin([6, 7, 8])].copy()
    print(f"School year data shape: {school_data.shape}")
    
    if len(school_data) == 0:
        print("⚠️ No school year data found, using all data for school model")
        school_data = df.copy()
    
    # Prepare features and target
    X = school_data.drop(columns=['Current Availability'])
    y = school_data['Current Availability']
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Grid Search
    param_grid = {
        'n_neighbors': [3, 5, 7, 9, 11],
        'weights': ['uniform', 'distance'],
        'metric': ['euclidean', 'manhattan']
    }
    
    knn = KNeighborsRegressor()
    grid_search = GridSearchCV(knn, param_grid, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)
    
    print("Training school year model...")
    grid_search.fit(X_train, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    
    # Evaluate
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"School Year Model Performance:")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE: {mae:.4f}")
    print(f"  R²: {r2:.4f}")
    print(f"  Best params: {grid_search.best_params_}")
    
    # Save model
    os.makedirs("schoolYear_model", exist_ok=True)
    joblib.dump(best_model, "schoolYear_model/best_school_knn.pkl")
    print("✅ School year model saved to schoolYear_model/best_school_knn.pkl")
    
    return best_model

if __name__ == "__main__":
    print("🚀 Training REAL ML Models for Parking Prediction")
    print("=" * 60)
    
    data_path = "../cyclic_1.csv"
    
    # Train all three models
    events_model = train_events_model(data_path)
    summer_model = train_summer_model(data_path)
    school_model = train_school_model(data_path)
    
    print("\n🎉 All models trained successfully!")
    print("Now updating prediction service to use real ML models...")