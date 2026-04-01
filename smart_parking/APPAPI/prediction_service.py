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

        self.zone_type_codes = {
            'Commuter': 0, 'Faculty': 1, 'Accessible': 2, 'EV': 3
        }
        self.deck_codes = {
            'Ballard': 0, 'Champions': 1, 'Chesapeake': 2,
            'Grace': 3, 'Mason': 4, 'Warsaw': 5
        }
        self.zone_types = {
            29: 'Accessible', 31: 'Accessible', 33: 'Accessible',
            35: 'Accessible', 37: 'Accessible', 38: 'Accessible',
            22: 'Commuter', 13: 'Commuter', 19: 'Commuter',
            4: 'Commuter', 3: 'Commuter', 42: 'Commuter',
            30: 'EV', 32: 'EV', 34: 'EV', 36: 'EV', 28: 'EV', 39: 'EV',
            27: 'Faculty', 40: 'Faculty', 6: 'Faculty', 12: 'Faculty', 2: 'Faculty'
        }
        self.zone_decks = {
            29: 'Ballard', 31: 'Champions', 33: 'Chesapeake', 35: 'Grace',
            37: 'Mason', 38: 'Warsaw',
            22: 'Ballard', 13: 'Champions', 19: 'Chesapeake', 4: 'Grace',
            3: 'Warsaw', 42: 'Warsaw',
            30: 'Ballard', 32: 'Champions', 34: 'Chesapeake', 36: 'Grace',
            28: 'Mason', 39: 'Warsaw',
            27: 'Ballard', 40: 'Champions', 6: 'Grace', 12: 'Mason', 2: 'Warsaw'
        }
        self.deck_distances = {
            'Ballard': {'Champions': 1.3, 'Chesapeake': 2.3, 'Grace': 2.1, 'Warsaw': 2.4},
            'Champions': {'Ballard': 1.3, 'Chesapeake': 1.6, 'Grace': 1.6, 'Warsaw': 1.3},
            'Chesapeake': {'Ballard': 2.3, 'Champions': 1.6, 'Grace': 1.7, 'Warsaw': 0.6},
            'Grace': {'Ballard': 2.1, 'Champions': 1.6, 'Chesapeake': 1.7, 'Warsaw': 0.6},
            'Warsaw': {'Ballard': 2.4, 'Champions': 1.3, 'Chesapeake': 0.6, 'Grace': 0.6},
        }
        self.summer_periods = [
            ('2024-05-12', '2024-08-20'),
            ('2025-05-15', '2025-08-19'),
        ]
        self.phase_codes = {
            'summer': 0,
            'move_in': 1,
            'first_two_weeks': 2,
            'regular_session': 3,
            'fall_break': 4,
            'thanksgiving_break': 5,
            'exam_week': 6,
            'winter_break': 7,
            'spring_break': 8,
            'unknown': 9,
        }
        self.campus_phases = [
            ('2024-04-01', '2024-05-09', 'regular_session'),
            ('2024-05-12', '2024-08-20', 'summer'),
            ('2024-08-21', '2024-08-25', 'move_in'),
            ('2024-08-26', '2024-09-06', 'first_two_weeks'),
            ('2024-09-07', '2024-10-15', 'regular_session'),
            ('2024-10-16', '2024-10-20', 'fall_break'),
            ('2024-10-21', '2024-11-24', 'regular_session'),
            ('2024-11-25', '2024-11-30', 'thanksgiving_break'),
            ('2024-12-01', '2024-12-08', 'regular_session'),
            ('2024-12-09', '2024-12-13', 'exam_week'),
            ('2024-12-14', '2025-01-12', 'winter_break'),
            ('2025-01-13', '2025-01-24', 'first_two_weeks'),
            ('2025-01-25', '2025-03-14', 'regular_session'),
            ('2025-03-15', '2025-03-22', 'spring_break'),
            ('2025-03-23', '2025-05-07', 'regular_session'),
            ('2025-05-08', '2025-05-14', 'exam_week'),
            ('2025-05-15', '2025-08-19', 'summer'),
            ('2025-08-20', '2025-08-24', 'move_in'),
            ('2025-08-25', '2025-09-05', 'first_two_weeks'),
            ('2025-09-06', '2025-10-14', 'regular_session'),
            ('2025-10-15', '2025-10-19', 'fall_break'),
            ('2025-10-20', '2025-11-23', 'regular_session'),
            ('2025-11-24', '2025-11-29', 'thanksgiving_break'),
            ('2025-11-30', '2025-12-05', 'regular_session'),
            ('2025-12-06', '2025-12-12', 'exam_week'),
            ('2025-12-13', '2026-01-11', 'winter_break'),
            ('2026-01-12', '2026-01-23', 'first_two_weeks'),
            ('2026-01-24', '2026-05-14', 'regular_session'),
        ]
        
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

    def _resolve_bundle_dir(self) -> str:
        """Resolve model bundle directory for the active production model set."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        smart_parking_root = os.path.dirname(current_dir)
        repo_root = os.path.dirname(smart_parking_root)

        bundle_dir = os.path.join(repo_root, 'final_ensemble', 'final_ensemble')
        if os.path.isdir(bundle_dir):
            return bundle_dir

        raise FileNotFoundError(
            "Required model bundle directory not found: "
            f"{bundle_dir}. Old model bundles are disabled."
        )

    def _normalize_lookup(self, lookup_obj):
        """Normalize lookup artifact to (zone-hour-dow, zone-hour) DataFrames."""
        if isinstance(lookup_obj, pd.DataFrame):
            return lookup_obj, None

        # Some pipelines save (lookup, lookup_zh). Use the first item.
        if isinstance(lookup_obj, tuple) and lookup_obj:
            first = lookup_obj[0]
            if isinstance(first, pd.DataFrame):
                second = lookup_obj[1] if len(lookup_obj) > 1 else None
                if second is not None and not isinstance(second, pd.DataFrame):
                    raise TypeError(
                        f"Unsupported secondary lookup type: {type(second).__name__}"
                    )
                return first, second

        raise TypeError(
            f"Unsupported lookup artifact type: {type(lookup_obj).__name__}"
        )
    
    def get_zone_for_garage(self, garage_name, zone_type='commuter'):
        """
        Get the zone ID for a specific garage and zone type.
        
        Args:
            garage_name (str): Name of the parking garage
            zone_type (str): Type of parking zone ('commuter', 'accessible', 'electric', 'faculty')
            
        Returns:
            int: Zone ID
        """
        # Try exact match first
        for garage_key, zones in self.garage_zones.items():
            if garage_key.lower() in garage_name.lower() or garage_name.lower() in garage_key.lower():
                zone_id = zones.get(zone_type)
                if zone_id is not None:
                    return zone_id
                raise ValueError(
                    f"Zone type '{zone_type}' is not available for garage '{garage_name}'"
                )

        raise ValueError(f"Unknown garage name: '{garage_name}'")

    def get_available_zone_types_for_garage(self, garage_name):
        """Return supported zone types for a garage based on configured zone IDs."""
        for garage_key, zones in self.garage_zones.items():
            if garage_key.lower() in garage_name.lower() or garage_name.lower() in garage_key.lower():
                return [zone for zone, zone_id in zones.items() if zone_id is not None]
        return []
    
    def _event_flags(self, arrival_time: datetime) -> dict:
        """Populate event flags from the exact step-5 mergeable event calendar."""
        flags = {event: 0 for event in self.event_columns}

        bundle_dir = self._resolve_bundle_dir()
        csv_path = os.path.join(bundle_dir, 'special_events-to-18MAR2026-mergeable.csv')
        if not os.path.isfile(csv_path):
            raise FileNotFoundError(
                "Required event calendar file not found: "
                f"{csv_path}. No fallback calendar is allowed."
            )

        events_df = pd.read_csv(csv_path)

        if 'Date' not in events_df.columns:
            raise ValueError("Event calendar is missing required 'Date' column.")

        missing_event_cols = [c for c in self.event_columns if c not in events_df.columns]
        if missing_event_cols:
            raise ValueError(
                "Event calendar is missing required event columns: "
                f"{missing_event_cols}"
            )

        events_df['Date'] = pd.to_datetime(events_df['Date'], errors='raise').dt.normalize()
        target_date = pd.to_datetime(arrival_time).normalize()
        event_row = events_df[events_df['Date'] == target_date]
        if not event_row.empty:
            for event in self.event_columns:
                flags[event] = int(event_row.iloc[0][event])
        return flags

    def _get_campus_phase_code(self, ts: pd.Timestamp) -> int:
        date_only = ts.normalize()
        for start_str, end_str, phase_label in self.campus_phases:
            if pd.Timestamp(start_str) <= date_only <= pd.Timestamp(end_str):
                return self.phase_codes[phase_label]
        return self.phase_codes['unknown']

    def _is_summer_date(self, ts: pd.Timestamp) -> bool:
        for start_str, end_str in self.summer_periods:
            if pd.Timestamp(start_str) <= ts <= pd.Timestamp(end_str) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1):
                return True
        return False

    def extract_features_from_arrival_time(self, arrival_time, garage_name, zone_type='commuter'):
        """
        Extract ML features from arrival time and garage information.
        Mirrors the LightGBM training pipelines (time features + stat lookup).
        """
        ts = pd.to_datetime(arrival_time)
        zone_id = self.get_zone_for_garage(garage_name, zone_type)
        event_flags = self._event_flags(ts)
        return self._extract_features_for_zone(ts, zone_id, event_flags)

    def _extract_features_for_zone(self, ts: pd.Timestamp, zone_id: int, event_flags: dict):
        """Build the exact feature schema expected by production sub-models."""

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
        features['zone_type'] = self.zone_type_codes.get(self.zone_types.get(zone_id, ''), -1)
        features['deck'] = self.deck_codes.get(self.zone_decks.get(zone_id, ''), -1)
        features['is_peak'] = 1 if 10 <= ts.hour <= 15 else 0
        features['hours_since_8am'] = max(0, ts.hour - 8)
        features['campus_phase'] = self._get_campus_phase_code(ts)

        # Event flags
        features.update(event_flags)
        features['is_event'] = 1 if any(event_flags.get(event, 0) for event in self.event_columns) else 0

        return features

    def _align_model_input(self, df: pd.DataFrame, model) -> pd.DataFrame:
        """Rename and reorder columns to exactly match LightGBM training feature names."""
        rename_map = {
            'Day of Week': 'Day_of_Week',
            'Ash Wednesday': 'Ash_Wednesday',
            'Easter Sunday': 'Easter_Sunday',
            'Exam Week': 'Exam_Week',
            'Fall Break': 'Fall_Break',
            'Family Weekend': 'Family_Weekend',
            'Home Football Game': 'Home_Football_Game',
            'Home Football Game (Homecoming)': 'Home_Football_Game_(Homecoming)',
            'Labor Day': 'Labor_Day',
            'Martin Luther King Jr. Day': 'Martin_Luther_King_Jr._Day',
            'Spring Break': 'Spring_Break',
            "St. Patrick&#39;s Day": "St._Patrick&#39;s_Day",
            'Thanksgiving Break': 'Thanksgiving_Break',
            'Winter Break': 'Winter_Break',
        }
        aligned = df.rename(columns=rename_map)

        expected = getattr(model, 'feature_name_', None)
        if expected is None:
            expected = getattr(model, 'feature_names_in_', None)
        if expected is None:
            raise ValueError("Model does not expose expected feature names.")

        missing = [col for col in expected if col not in aligned.columns]
        if missing:
            raise ValueError(f"Model input is missing required features: {missing}")

        extra = [col for col in aligned.columns if col not in expected]
        if extra:
            raise ValueError(f"Model input contains unexpected features: {extra}")

        return aligned[list(expected)]
    
    def load_models(self):
        """Load LightGBM models and stat lookup tables from the new bundle."""
        if self.models_loaded:
            return True

        bundle_dir = self._resolve_bundle_dir()

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

        self.events_lookup = self._normalize_lookup(joblib.load(events_lookup_path))
        self.summer_lookup = self._normalize_lookup(joblib.load(summer_lookup_path))
        self.school_lookup = self._normalize_lookup(joblib.load(school_lookup_path))

        print("All LightGBM models and lookup tables loaded successfully!")
        self.models_loaded = True
        return True
    
    def classify_time_period(self, ts: pd.Timestamp, event_flags: dict):
        """Classify whether prediction should use events, summer, or school-year model."""
        if any(event_flags.get(event, 0) for event in self.event_columns):
            return 'events'
        if self._is_summer_date(ts):
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
        try:
            # Load models if needed
            self.load_models()

            ts = pd.to_datetime(arrival_time)
            target_zone = self.get_zone_for_garage(garage_name, zone_type)
            event_flags = self._event_flags(ts)
            model_type = self.classify_time_period(ts, event_flags)

            base_predictions = self._predict_zone_group(ts, target_zone, model_type, event_flags)
            predicted_spaces = self._apply_spatial_adjustment(target_zone, base_predictions)
            features = self._extract_features_for_zone(ts, target_zone, event_flags)
            confidence = self._calculate_confidence(features, model_type)
            zone_capacity = features['zone_capacity']
            if zone_capacity <= 0:
                raise ValueError(f"Invalid zone capacity for zone {features['Zone']}: {zone_capacity}")

            return {
                'predicted_spaces': predicted_spaces,
                'availability_percentage': min(100, max(0, (predicted_spaces / zone_capacity) * 100)),
                'confidence': confidence,
                'model_used': model_type,
                'zone_id': features['Zone'],
                'features': features
            }
        except ValueError as e:
            return {
                'error': True,
                'error_type': 'validation',
                'message': str(e),
                'garage_name': garage_name,
                'zone_type': zone_type,
                'available_zone_types': self.get_available_zone_types_for_garage(garage_name),
            }
        except Exception as e:
            return {
                'error': True,
                'error_type': 'runtime',
                'message': f'Real ML model prediction failed: {str(e)}',
                'garage_name': garage_name,
                'zone_type': zone_type,
            }
    
    def _apply_lookup(self, df: pd.DataFrame, lookup_pair: Tuple[pd.DataFrame, pd.DataFrame]) -> pd.DataFrame:
        lookup, lookup_zh = lookup_pair
        df = df.merge(lookup, on=['Zone', 'hour', 'Day of Week'], how='left')

        if lookup_zh is not None:
            df = df.merge(lookup_zh, on=['Zone', 'hour'], how='left')

        required_cols = ['hist_mean', 'hist_std']
        if lookup_zh is not None:
            required_cols.extend(['hist_mean_zh', 'hist_std_zh'])

        missing_required = [col for col in required_cols if col not in df.columns]
        if missing_required:
            raise ValueError(f"Lookup merge missing required columns: {missing_required}")

        if any(df[col].isna().any() for col in required_cols):
            raise ValueError(
                "Lookup merge produced missing historical feature values; "
                "no fallback fill is allowed."
            )
        return df

    def _predict_with_real_models(self, features, model_type):
        """Use the LightGBM models with per-model feature expectations."""
        try:
            base_df = pd.DataFrame([features])

            # Apply stat lookup per routed model and drop event cols where applicable
            if model_type == 'events':
                df = self._apply_lookup(base_df, self.events_lookup)
                model_input = self._align_model_input(
                    df.drop(columns=['Timestamp'], errors='ignore'),
                    self.events_model,
                )
                occupancy_rate = float(self.events_model.predict(model_input)[0])
                print(f"Used Events LGBM occupancy: {occupancy_rate:.4f}")
            elif model_type == 'summer':
                df = base_df.drop(columns=self.event_columns + ['is_event'], errors='ignore')
                df = self._apply_lookup(df, self.summer_lookup)
                model_input = self._align_model_input(
                    df.drop(columns=['Timestamp'], errors='ignore'),
                    self.summer_model,
                )
                occupancy_rate = float(self.summer_model.predict(model_input)[0])
                print(f"Used Summer LGBM occupancy: {occupancy_rate:.4f}")
            else:  # school
                df = base_df.drop(columns=self.event_columns + ['is_event'], errors='ignore')
                df = self._apply_lookup(df, self.school_lookup)
                model_input = self._align_model_input(
                    df.drop(columns=['Timestamp'], errors='ignore'),
                    self.school_model,
                )
                occupancy_rate = float(self.school_model.predict(model_input)[0])
                print(f"Used School LGBM occupancy: {occupancy_rate:.4f}")

            occupancy_rate = min(1.0, max(0.0, occupancy_rate))
            zone_capacity = features['zone_capacity']
            if zone_capacity <= 0:
                raise ValueError(f"Invalid zone capacity for zone {features['Zone']}: {zone_capacity}")

            predicted_spaces = zone_capacity * (1.0 - occupancy_rate)
            return max(0, int(round(predicted_spaces)))

        except Exception as e:
            print(f"Error in model prediction: {e}")
            print(f"Features: {features}")
            print(f"Model type: {model_type}")
            raise RuntimeError(f"ML model prediction failed: {e}")

    def _predict_zone_group(self, ts: pd.Timestamp, target_zone: int, model_type: str, event_flags: dict) -> dict:
        """Predict base available spaces for all zones sharing the target permit type."""
        target_type = self.zone_types.get(target_zone)
        if target_type is None:
            raise ValueError(f"Unsupported target zone for spatial prediction: {target_zone}")

        relevant_zones = [zone for zone, ztype in self.zone_types.items() if ztype == target_type]
        if not relevant_zones:
            raise ValueError(f"No relevant zones found for permit type: {target_type}")

        predictions = {}
        for zone in relevant_zones:
            features = self._extract_features_for_zone(ts, zone, event_flags)
            predictions[zone] = self._predict_with_real_models(features, model_type)
        return predictions

    def _apply_spatial_adjustment(self, target_zone: int, base_predictions: dict, alpha: float = 0.05,
                                  power: int = 2, congestion_threshold: float = 0.90) -> int:
        """Apply the step-5 gravity adjustment to the target zone prediction."""
        if target_zone not in base_predictions:
            raise ValueError(f"Missing base prediction for target zone: {target_zone}")

        target_deck = self.zone_decks.get(target_zone)
        target_type = self.zone_types.get(target_zone)
        target_cap = self._zone_capacity_for(target_zone)
        if target_deck is None or target_type is None:
            raise ValueError(f"Missing deck/type metadata for target zone: {target_zone}")
        if target_deck not in self.deck_distances:
            raise ValueError(f"Missing distance matrix for target deck: {target_deck}")

        pressure = 0.0
        for zone, available in base_predictions.items():
            if zone == target_zone:
                continue
            zone_type = self.zone_types.get(zone)
            if zone_type != target_type:
                continue

            other_deck = self.zone_decks.get(zone)
            other_cap = self._zone_capacity_for(zone)
            if other_deck is None:
                raise ValueError(f"Missing deck metadata for zone: {zone}")
            if other_deck not in self.deck_distances[target_deck]:
                continue

            distance = self.deck_distances[target_deck][other_deck]
            fullness = 1.0 - max(0.0, min(1.0, available / other_cap))
            if fullness > congestion_threshold:
                pressure += fullness / (distance ** power)

        adjusted = base_predictions[target_zone] - (pressure * target_cap * alpha)
        return max(0, min(target_cap, int(round(adjusted))))

    def _zone_capacity_for(self, zone_id: int) -> int:
        zone_capacities = {
            29: 31,   31: 8,    33: 13,   35: 12,   37: 17,   38: 17,
            22: 1462, 13: 451,  19: 630,  4: 389,   3: 599,   42: 599,
            30: 2,    32: 4,    34: 2,    36: 3,    28: 4,    39: 4,
            27: 87,   40: 13,   6: 55,    12: 570,  2: 177
        }
        capacity = zone_capacities.get(zone_id)
        if capacity is None or capacity <= 0:
            raise ValueError(f"Invalid or missing capacity for zone: {zone_id}")
        return capacity
    
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