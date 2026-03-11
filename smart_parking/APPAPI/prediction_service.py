"""
Parking Prediction Service

This module provides real-time parking availability predictions using the existing ensemble model.
It handles feature extraction from arrival time and garage selection, then returns predictions.
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import math
import os
from typing import Tuple


class ParkingPredictionService:
    def __init__(self):
        """Initialize the prediction service with garage mappings and event calendars."""
        
        # JMU Parking Garage Zone Mappings (based on the data analysis)
        self.garage_zones = {
            'Chesapeake Hall Parking Deck': {
                'accessible': 33, 'commuter': 19, 'electric': 34
            },
            'Grace Street Parking Deck': {
                'accessible': 35, 'commuter': 4, 'electric': 36, 'faculty': 6  
            },
            'Warsaw Avenue Parking Deck': {
                'accessible': 38, 'commuter': 42, 'electric': 39, 'faculty': 41
            },
            'Champions Drive Parking Deck': {
                'accessible': 31, 'commuter': 13, 'electric': 40, 'faculty': 32
            },
            'Ballard Hall Parking Deck': {
                'accessible': 29, 'commuter': 22, 'electric': 30, 'faculty': 27
            },
            'Mason Parking Deck': {
                'accessible': 37, 'commuter': None, 'electric': 28, 'faculty': 12
            }
        }
        
        # Event calendar flags (expanded to align with new LGBM models)
        self.event_columns = [
            'Ash Wednesday', 'Commencement', 'Easter Sunday', 'Exam Week',
            'Fall Break', 'Family Weekend', 'Home Football Game',
            'Home Football Game (Homecoming)', 'Labor Day',
            'Martin Luther King Jr. Day', 'Spring Break',
            "St. Patrick&#39;s Day", 'Thanksgiving Break', 'Winter Break'
        ]
        
        # Models + lookup tables will be loaded lazily
        self.models_loaded = False
        self.events_model = None
        self.summer_model = None  
        self.school_model = None
        self.events_lookup = None
        self.summer_lookup = None
        self.school_lookup = None
    
    def get_zone_for_garage(self, garage_name, zone_type='commuter'):
        """
        Get the zone ID for a specific garage and zone type.
        
        Args:
            garage_name (str): Name of the parking garage
            zone_type (str): Type of parking zone ('commuter', 'accessible', 'electric', 'faculty')
            
        Returns:
            int: Zone ID, or default commuter zone if not found
        """
        # Try exact match first
        for garage_key, zones in self.garage_zones.items():
            if garage_key.lower() in garage_name.lower() or garage_name.lower() in garage_key.lower():
                zone_id = zones.get(zone_type)
                if zone_id is not None:
                    return zone_id
                # Fallback to commuter if requested type not available
                return zones.get('commuter', 22)  # Default to Ballard commuter
        
        # Default fallback
        return 22  # Ballard commuter zone as default
    
    def _event_flags(self, arrival_time: datetime) -> dict:
        """Populate event flags from CSV if columns exist, otherwise zeros."""
        flags = {event: 0 for event in self.event_columns}
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        csv_path = os.path.join(project_root, 'event_pulling', 'special_event_mergable2.csv')
        try:
            events_df = pd.read_csv(csv_path)
            arrival_date_str = arrival_time.strftime('%m/%d/%Y')
            event_row = events_df[events_df['Date'] == arrival_date_str]
            if not event_row.empty:
                for event in self.event_columns:
                    if event in event_row.columns:
                        flags[event] = int(event_row.iloc[0][event])
        except Exception as e:
            print(f"Error reading events CSV: {e}")
        return flags

    def extract_features_from_arrival_time(self, arrival_time, garage_name, zone_type='commuter'):
        """
        Extract ML features from arrival time and garage information.
        Mirrors the LightGBM training pipelines (time features + stat lookup).
        """
        ts = pd.to_datetime(arrival_time)
        zone_id = self.get_zone_for_garage(garage_name, zone_type)

        # Base time/zone features
        total_minutes = ts.hour * 60 + ts.minute
        features = {
            'Timestamp': ts,
            'Zone': zone_id,
            'Day of Week': ts.weekday(),  # 0=Mon
            'month': ts.month,
            'time_sin': math.sin(2 * math.pi * total_minutes / 1440),
            'time_cos': math.cos(2 * math.pi * total_minutes / 1440),
            'hour': ts.hour,
            'minute': ts.minute,
            'doy_sin': math.sin(2 * math.pi * ts.dayofyear / 365),
            'doy_cos': math.cos(2 * math.pi * ts.dayofyear / 365),
            'woy_sin': math.sin(2 * math.pi * ts.isocalendar().week / 52),
            'woy_cos': math.cos(2 * math.pi * ts.isocalendar().week / 52),
            'is_weekend': 1 if ts.weekday() >= 5 else 0,
        }

        # Zone capacity feature aligns with training constants in partner models
        zone_capacities = {
            29: 31,   31: 8,    33: 13,   35: 12,   37: 17,   38: 17,
            22: 1462, 13: 451,  19: 630,  4:  389,  3:  599,  42: 599,
            30: 2,    32: 4,    34: 2,    36: 3,    28: 4,    39: 4,
            27: 87,   40: 13,   6:  55,   12: 570,  2:  177
        }
        features['zone_capacity'] = zone_capacities.get(zone_id, 0)

        # Event flags
        features.update(self._event_flags(ts))

        return features
    
    def load_models(self):
        """Load LightGBM models and stat lookup tables from the new bundle."""
        if self.models_loaded:
            return True
            
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            bundle_dir = os.path.join(project_root, 'esnemble_model', 'esnemble_model')

            events_model_path = os.path.join(bundle_dir, 'best_events_lgbm_production.pkl')
            summer_model_path = os.path.join(bundle_dir, 'best_summer_lgbm_production.pkl')
            school_model_path = os.path.join(bundle_dir, 'best_schoolyear_lgbm_production.pkl')

            events_lookup_path = os.path.join(bundle_dir, 'events_stat_lookup_production.pkl')
            summer_lookup_path = os.path.join(bundle_dir, 'summer_stat_lookup_production.pkl')
            school_lookup_path = os.path.join(bundle_dir, 'schoolyear_stat_lookup_production.pkl')

            print("Loading models and lookups from:")
            print(f"  Events model:  {events_model_path}")
            print(f"  Summer model:  {summer_model_path}")
            print(f"  School model:  {school_model_path}")
            print(f"  Events lookup: {events_lookup_path}")
            print(f"  Summer lookup: {summer_lookup_path}")
            print(f"  School lookup: {school_lookup_path}")

            self.events_model = joblib.load(events_model_path)
            self.summer_model = joblib.load(summer_model_path)
            self.school_model = joblib.load(school_model_path)

            self.events_lookup = joblib.load(events_lookup_path)
            self.summer_lookup = joblib.load(summer_lookup_path)
            self.school_lookup = joblib.load(school_lookup_path)

            print("All LightGBM models and lookup tables loaded successfully!")
            self.models_loaded = True
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def classify_time_period(self, features):
        """Classify whether prediction should use events, summer, or school-year model."""
        if any(features.get(event, 0) for event in self.event_columns):
            return 'events'
        if features['month'] in [5, 6, 7]:  # summer excludes August
            return 'summer'
        return 'school'
    
    def predict_availability(self, arrival_time, garage_name, zone_type='commuter'):
        """
        Predict parking availability for the given arrival time and garage.
        
        Args:
            arrival_time (datetime): When the user expects to arrive
            garage_name (str): Name of the parking garage
            zone_type (str): Type of parking zone
            
        Returns:
            dict: Prediction results including availability estimate and confidence
        """
        # Load models if needed
        if not self.load_models():
            return {
                'error': 'Models not available',
                'availability': None,
                'confidence': 0,
                'model_used': None
            }
        
        # Extract features
        features = self.extract_features_from_arrival_time(arrival_time, garage_name, zone_type)
        model_type = self.classify_time_period(features)

        try:
            predicted_spaces = self._predict_with_real_models(features, model_type)
            confidence = self._calculate_confidence(features, model_type)
            return {
                'predicted_spaces': predicted_spaces,
                'availability_percentage': min(100, max(0, (predicted_spaces / 100) * 100)),
                'confidence': confidence,
                'model_used': model_type,
                'zone_id': features['Zone'],
                'features': features
            }
        except Exception as e:
            return {
                'error': True,
                'message': f'Real ML model prediction failed: {str(e)}',
                'model_type': model_type,
                'zone_id': features['Zone'],
                'features': features
            }
    
    def _apply_lookup(self, df: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
        df = df.merge(lookup, on=['Zone', 'hour', 'Day of Week'], how='left')
        df['hist_mean'] = df['hist_mean'].fillna(df['hist_mean'].median())
        df['hist_std'] = df['hist_std'].fillna(0)
        return df

    def _predict_with_real_models(self, features, model_type):
        """Use the LightGBM models with per-model feature expectations."""
        try:
            base_df = pd.DataFrame([features])

            # Apply stat lookup per routed model and drop event cols where applicable
            if model_type == 'events':
                df = self._apply_lookup(base_df, self.events_lookup)
                prediction = float(self.events_model.predict(df.drop(columns=['Timestamp'], errors='ignore'))[0])
                print(f"Used Events LGBM: {prediction:.1f} spaces")
            elif model_type == 'summer':
                df = base_df.drop(columns=self.event_columns, errors='ignore')
                df = self._apply_lookup(df, self.summer_lookup)
                prediction = float(self.summer_model.predict(df.drop(columns=['Timestamp'], errors='ignore'))[0])
                print(f"Used Summer LGBM: {prediction:.1f} spaces")
            else:  # school
                df = base_df.drop(columns=self.event_columns, errors='ignore')
                df = self._apply_lookup(df, self.school_lookup)
                prediction = float(self.school_model.predict(df.drop(columns=['Timestamp'], errors='ignore'))[0])
                print(f"Used School LGBM: {prediction:.1f} spaces")

            prediction = max(0, int(round(prediction)))
            return prediction

        except Exception as e:
            print(f"Error in model prediction: {e}")
            print(f"Features: {features}")
            print(f"Model type: {model_type}")
            raise RuntimeError(f"ML model prediction failed: {e}")
    
    def _handle_prediction_failure(self, error_message, features, model_type):
        """Handle ML model prediction failures by returning error info."""
        return {
            'error': True,
            'message': f'ML model prediction failed: {error_message}',
            'model_type': model_type,
            'features_attempted': features
        }
    
    def _calculate_confidence(self, features, model_type):
        """Calculate prediction confidence based on various factors."""
        
        confidence = 0.7  # Base confidence
        
        # Higher confidence during regular patterns
        hour = (features['time_cos'] + 1) * 12  # Convert to rough hour
        if 8 <= hour <= 18:  # Regular business hours
            confidence += 0.2
        
        # Lower confidence during events
        if any(features[event] for event in self.event_columns):
            confidence -= 0.1
        
        # Model-specific confidence
        if model_type == 'school':
            confidence += 0.1  # School year patterns are most reliable
        elif model_type == 'events':
            confidence -= 0.1  # Events are less predictable
        
        return min(0.95, max(0.3, confidence))


# Global service instance
prediction_service = ParkingPredictionService()


def predict_parking_availability(arrival_datetime, garage_name, zone_type='commuter'):
    """
    Main function to get parking availability prediction.
    
    Args:
        arrival_datetime (datetime): When the user expects to arrive
        garage_name (str): Name of the parking garage
        zone_type (str): Type of parking zone ('commuter', 'accessible', 'electric', 'faculty')
        
    Returns:
        dict: Prediction results
    """
    return prediction_service.predict_availability(arrival_datetime, garage_name, zone_type)