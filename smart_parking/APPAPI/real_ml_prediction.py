#!/usr/bin/env python3
"""
REAL parking prediction service using the trained ML ensemble models
This uses the actual KNN models trained by the previous group
"""

import datetime
import pandas as pd
import numpy as np
import math
import joblib
import os

# Load the trained models once when the module is imported
print("Loading trained ML models...")
try:
    events_model = joblib.load('/home/rosalejg/Downloads/smart-parking-capstone-main/ensemble_ML/events_model/best_events_knn.pkl')
    summer_model = joblib.load('/home/rosalejg/Downloads/smart-parking-capstone-main/ensemble_ML/summer_model/best_summer_knn.pkl')  
    school_model = joblib.load('/home/rosalejg/Downloads/smart-parking-capstone-main/ensemble_ML/schoolYear_model/best_school_knn.pkl')
    print("✅ All ML models loaded successfully!")
except Exception as e:
    print(f"❌ Error loading models: {e}")
    events_model = summer_model = school_model = None

def extract_features_from_arrival_time(arrival_time, garage_name):
    """
    Extract features from arrival time to match the training data format
    """
    # Parse arrival time
    arrival_dt = datetime.datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
    
    # Zone mapping (garage name to zone ID from training data)
    zone_mapping = {
        'Commuter Deck': 22,
        'East Campus Deck': 13, 
        'Grace St Deck': 19,
        'Warsaw Ave Deck': 4,
        'Warsaw Ave Lot': 27,
        'Godwin Bus Lot': 15,
        'Hillside Hall Lot': 8,
        'Mason St Lot': 11,
        'Bluestone Drive Lot': 6,
        'Carrier Dr Lot': 9,
        'Lakeside Lot': 17
    }
    
    zone = zone_mapping.get(garage_name, 22)  # Default to Commuter Deck zone if not found
    
    # Extract temporal features
    day_of_week = arrival_dt.weekday() + 1  # Monday = 1
    month = arrival_dt.month
    
    # Calculate time as minutes from midnight for cyclical encoding
    time_minutes = arrival_dt.hour * 60 + arrival_dt.minute
    
    # Cyclical time encoding (24-hour cycle)
    time_sin = math.sin(2 * math.pi * time_minutes / (24 * 60))
    time_cos = math.cos(2 * math.pi * time_minutes / (24 * 60))
    
    # Simple event detection based on date/time patterns
    # This is a simplified version - the real system would have a proper event calendar
    fall_break = 1 if month == 10 and arrival_dt.day in range(15, 22) else 0
    family_weekend = 1 if month == 9 and arrival_dt.weekday() in [5, 6] else 0
    
    # Football game detection (simplified - Saturdays in fall)
    home_football_game = 1 if month in [9, 10, 11] and arrival_dt.weekday() == 5 else 0
    homecoming = 1 if month == 10 and arrival_dt.weekday() == 5 and arrival_dt.day in range(14, 21) else 0
    labor_day = 1 if month == 9 and arrival_dt.day <= 7 and arrival_dt.weekday() == 0 else 0
    
    # Return features in the same order as training data
    features = {
        'Zone': zone,
        'Day of Week': day_of_week,
        'month': month,
        'time_sin': time_sin,
        'time_cos': time_cos,
        'Fall Break': fall_break,
        'Family Weekend': family_weekend,
        'Home Football Game': home_football_game,
        'Home Football Game (Homecoming)': homecoming,
        'Labor Day': labor_day
    }
    
    return features

def classify_prediction_type(arrival_time):
    """
    Classify which model to use based on time/date
    Returns: 'events', 'summer', or 'school'
    """
    arrival_dt = datetime.datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
    month = arrival_dt.month
    
    # Check for events first (simplified event detection)
    if month in [9, 10, 11] and arrival_dt.weekday() in [5, 6]:  # Fall weekends
        return 'events'
    elif month == 10 and arrival_dt.day in range(15, 22):  # Fall break
        return 'events'
    elif month == 9 and arrival_dt.day <= 7 and arrival_dt.weekday() == 0:  # Labor day
        return 'events'
    
    # Summer vs school year
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'school'

def predict_availability(arrival_time, garage_name):
    """
    Main prediction function using REAL TRAINED ML MODELS
    """
    try:
        # Extract features
        features = extract_features_from_arrival_time(arrival_time, garage_name)
        prediction_type = classify_prediction_type(arrival_time)
        
        print(f"🎯 Using {prediction_type} model for prediction")
        print(f"📊 Features: {features}")
        
        # Convert features to DataFrame for model prediction
        feature_df = pd.DataFrame([features])
        
        # Select the appropriate trained model
        if prediction_type == 'events' and events_model is not None:
            prediction = events_model.predict(feature_df)[0]
            print(f"🎪 Events model prediction: {prediction}")
        elif prediction_type == 'summer' and summer_model is not None:
            prediction = summer_model.predict(feature_df)[0]
            print(f"☀️ Summer model prediction: {prediction}")
        elif prediction_type == 'school' and school_model is not None:
            prediction = school_model.predict(feature_df)[0]
            print(f"🏫 School model prediction: {prediction}")
        else:
            # Fallback if models aren't loaded
            print("⚠️ Model not available, using fallback calculation")
            arrival_dt = datetime.datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            hour = arrival_dt.hour
            
            base_capacity = {
                'Commuter Deck': 800,
                'East Campus Deck': 600,
                'Grace St Deck': 400,
                'Warsaw Ave Deck': 300,
                'Warsaw Ave Lot': 200,
                'Godwin Bus Lot': 150,
                'Hillside Hall Lot': 100,
                'Mason St Lot': 80,
                'Bluestone Drive Lot': 120,
                'Carrier Dr Lot': 90,
                'Lakeside Lot': 110
            }.get(garage_name, 500)
            
            if hour in [8, 9, 12, 13]:
                prediction = max(0, base_capacity * 0.1)
            else:
                prediction = base_capacity * 0.4
        
        # Ensure prediction is a reasonable integer
        result = int(max(0, round(prediction)))
        print(f"🎯 Final prediction: {result} available spaces")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in prediction: {e}")
        return 100  # Default fallback