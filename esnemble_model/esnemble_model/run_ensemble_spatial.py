"""
Ensemble + Spatial Pipeline — Production Version
=================================================
Loads the three production LightGBM models and their stat lookup tables.
Handles all feature engineering identically to training scripts.

Run this after training all three sub-models.

INPUTS  (place in same directory):
  best_summer_lgbm_production.pkl
  best_events_lgbm_production.pkl
  best_schoolyear_lgbm_production.pkl
  summer_stat_lookup_production.pkl
  events_stat_lookup_production.pkl
  schoolyear_stat_lookup_production.pkl

OUTPUT:
  final_predictions.csv
"""

import pandas as pd
import numpy as np
import joblib
import time
import warnings
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    explained_variance_score, mean_absolute_percentage_error
)

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Zone / spatial config
# ---------------------------------------------------------------------------
ZONE_INFO = {
    29: {'deck': 'Ballard',    'type': 'Accessible', 'cap': 31},
    31: {'deck': 'Champions',  'type': 'Accessible', 'cap': 8},
    33: {'deck': 'Chesapeake', 'type': 'Accessible', 'cap': 13},
    35: {'deck': 'Grace',      'type': 'Accessible', 'cap': 12},
    37: {'deck': 'Mason',      'type': 'Accessible', 'cap': 17},
    38: {'deck': 'Warsaw',     'type': 'Accessible', 'cap': 17},
    22: {'deck': 'Ballard',    'type': 'Commuter',   'cap': 1462},
    13: {'deck': 'Champions',  'type': 'Commuter',   'cap': 451},
    19: {'deck': 'Chesapeake', 'type': 'Commuter',   'cap': 630},
     4: {'deck': 'Grace',      'type': 'Commuter',   'cap': 389},
     3: {'deck': 'Warsaw',     'type': 'Commuter',   'cap': 599},
    42: {'deck': 'Warsaw',     'type': 'Commuter',   'cap': 599},
    30: {'deck': 'Ballard',    'type': 'EV',         'cap': 2},
    32: {'deck': 'Champions',  'type': 'EV',         'cap': 4},
    34: {'deck': 'Chesapeake', 'type': 'EV',         'cap': 2},
    36: {'deck': 'Grace',      'type': 'EV',         'cap': 3},
    28: {'deck': 'Mason',      'type': 'EV',         'cap': 4},
    39: {'deck': 'Warsaw',     'type': 'EV',         'cap': 4},
    27: {'deck': 'Ballard',    'type': 'Faculty',    'cap': 87},
    40: {'deck': 'Champions',  'type': 'Faculty',    'cap': 13},
     6: {'deck': 'Grace',      'type': 'Faculty',    'cap': 55},
    12: {'deck': 'Mason',      'type': 'Faculty',    'cap': 570},
     2: {'deck': 'Warsaw',     'type': 'Faculty',    'cap': 177},
}

ZONE_CAPACITIES = {z: v['cap'] for z, v in ZONE_INFO.items()}

DECK_DISTANCES = {
    'Ballard':    {'Champions': 1.3, 'Chesapeake': 2.3, 'Grace': 2.1, 'Warsaw': 2.4},
    'Champions':  {'Ballard':   1.3, 'Chesapeake': 1.6, 'Grace': 1.6, 'Warsaw': 1.3},
    'Chesapeake': {'Ballard':   2.3, 'Champions':  1.6, 'Grace': 1.7, 'Warsaw': 0.6},
    'Grace':      {'Ballard':   2.1, 'Champions':  1.6, 'Chesapeake': 1.7, 'Warsaw': 0.6},
    'Warsaw':     {'Ballard':   2.4, 'Champions':  1.3, 'Chesapeake': 0.6, 'Grace': 0.6},
}

EVENT_COLUMNS = [
    'Ash Wednesday', 'Commencement', 'Easter Sunday', 'Exam Week',
    'Fall Break', 'Family Weekend', 'Home Football Game',
    'Home Football Game (Homecoming)', 'Labor Day',
    'Martin Luther King Jr. Day', 'Spring Break',
    "St. Patrick&#39;s Day", 'Thanksgiving Break', 'Winter Break'
]

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def adjusted_mape(y_true, y_pred):
    mask = np.array(y_true) != 0
    return mean_absolute_percentage_error(
        np.array(y_true)[mask], np.array(y_pred)[mask]
    ) * 100


def print_scores(name, y_true, y_pred, elapsed=None):
    rmse   = np.sqrt(mean_squared_error(y_true, y_pred))
    mae    = mean_absolute_error(y_true, y_pred)
    mape   = adjusted_mape(y_true, y_pred)
    r2     = r2_score(y_true, y_pred)
    ev     = explained_variance_score(y_true, y_pred)
    n      = len(y_true)
    adj_r2 = 1 - ((1 - r2) * (n - 1) / (n - 2))
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    print(f"  RMSE:         {rmse:.4f}")
    print(f"  MAE:          {mae:.4f}")
    print(f"  MAPE:         {mape:.2f}%")
    print(f"  R2:           {r2:.4f}")
    print(f"  Adjusted R2:  {adj_r2:.4f}")
    print(f"  EV:           {ev:.4f}")
    if elapsed is not None:
        print(f"  Time:         {elapsed:.3f}s")
    print(f"{'='*50}\n")

# ---------------------------------------------------------------------------
# Feature engineering — MUST match training scripts exactly
# ---------------------------------------------------------------------------
def add_time_features(df):
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['hour']      = df['Timestamp'].dt.hour
    df['minute']    = df['Timestamp'].dt.minute

    doy = df['Timestamp'].dt.dayofyear
    df['doy_sin'] = np.sin(2 * np.pi * doy / 365)
    df['doy_cos'] = np.cos(2 * np.pi * doy / 365)

    woy = df['Timestamp'].dt.isocalendar().week.astype(int)
    df['woy_sin'] = np.sin(2 * np.pi * woy / 52)
    df['woy_cos'] = np.cos(2 * np.pi * woy / 52)

    df['is_weekend']    = (df['Day of Week'] >= 5).astype(int)
    df['zone_capacity'] = df['Zone'].map(ZONE_CAPACITIES).fillna(0).astype(int)
    return df


def apply_stat_lookup(df, lookup):
    df = df.merge(lookup, on=['Zone', 'hour', 'Day of Week'], how='left')
    df['hist_mean'] = df['hist_mean'].fillna(df['hist_mean'].median())
    df['hist_std']  = df['hist_std'].fillna(0)
    return df

# ---------------------------------------------------------------------------
# Ensemble routing
# ---------------------------------------------------------------------------
def classify_rows(X):
    event_mask  = X[EVENT_COLUMNS].sum(axis=1) > 0
    summer_mask = X['month'].isin([5, 6, 7]) & ~event_mask
    school_mask = ~event_mask & ~summer_mask
    return event_mask, summer_mask, school_mask


def ensemble_predict(X_test, events_model, summer_model, school_model,
                     events_lookup, summer_lookup, school_lookup):
    """
    Routes each row to its sub-model, applying the correct stat lookup
    per sub-model (lookup tables are model-specific).
    """
    pred = np.empty(len(X_test))
    event_mask, summer_mask, school_mask = classify_rows(X_test)

    print(f"  Event rows:  {event_mask.sum():,}")
    print(f"  Summer rows: {summer_mask.sum():,}")
    print(f"  School rows: {school_mask.sum():,}")

    # Events — keep event columns, apply events lookup
    if event_mask.any():
        X_ev = apply_stat_lookup(X_test[event_mask].copy(), events_lookup)
        pred[event_mask.values] = events_model.predict(
            X_ev.drop(columns=['Current Availability', 'Timestamp'], errors='ignore')
        )

    # Summer — drop event columns, apply summer lookup
    if summer_mask.any():
        X_su = X_test[summer_mask].drop(columns=EVENT_COLUMNS, errors='ignore').copy()
        X_su = apply_stat_lookup(X_su, summer_lookup)
        pred[summer_mask.values] = summer_model.predict(
            X_su.drop(columns=['Current Availability', 'Timestamp'], errors='ignore')
        )

    # School year — drop event columns, apply school lookup
    if school_mask.any():
        X_sc = X_test[school_mask].drop(columns=EVENT_COLUMNS, errors='ignore').copy()
        X_sc = apply_stat_lookup(X_sc, school_lookup)
        pred[school_mask.values] = school_model.predict(
            X_sc.drop(columns=['Current Availability', 'Timestamp'], errors='ignore')
        )

    return pred

# ---------------------------------------------------------------------------
# Spatial gravity model
# ---------------------------------------------------------------------------
def apply_spatial_model(predictions_df, alpha=0.05, power=2, congestion_threshold=0.90):
    print(f"  Spatial: alpha={alpha}, power={power}, threshold={congestion_threshold}")
    spatial_df = predictions_df.copy()
    spatial_df['Spatially_Adjusted_Pred'] = spatial_df['Base_Predicted'].astype(float)

    for timestamp, group in spatial_df.groupby('Timestamp'):
        current_preds = dict(zip(group['Zone'], group['Base_Predicted']))

        for idx, row in group.iterrows():
            zone = row['Zone']
            if zone not in ZONE_INFO:
                continue
            meta   = ZONE_INFO[zone]
            deck   = meta['deck']
            p_type = meta['type']
            cap    = meta['cap']

            if deck not in DECK_DISTANCES:
                continue

            pressure = 0.0
            for nz, na in current_preds.items():
                if nz == zone or nz not in ZONE_INFO:
                    continue
                nm = ZONE_INFO[nz]
                if nm['type'] == p_type and nm['deck'] in DECK_DISTANCES.get(deck, {}):
                    dist       = DECK_DISTANCES[deck][nm['deck']]
                    fullness   = 1.0 - max(0.0, min(1.0, na / nm['cap']))
                    if fullness > congestion_threshold:
                        pressure += fullness / (dist ** power)

            adjusted = max(0.0, min(float(cap), row['Base_Predicted'] - pressure * cap * alpha))
            spatial_df.at[idx, 'Spatially_Adjusted_Pred'] = adjusted

    return spatial_df

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run_pipeline():
    # Load models
    print("Loading models...", flush=True)
    events_model = joblib.load('/Users/michaelcraig/Desktop/lgbm_files/best_events_lgbm_production.pkl')
    summer_model = joblib.load('/Users/michaelcraig/Desktop/lgbm_files/best_summer_lgbm_production.pkl')
    school_model = joblib.load('/Users/michaelcraig/Desktop/lgbm_files/best_schoolyear_lgbm_production.pkl')

    # Load stat lookups (must match each model)
    events_lookup = joblib.load('/Users/michaelcraig/Desktop/lgbm_files/events_stat_lookup_production.pkl')
    summer_lookup = joblib.load('/Users/michaelcraig/Desktop/lgbm_files/summer_stat_lookup_production.pkl')
    school_lookup = joblib.load('/Users/michaelcraig/Desktop/lgbm_files/schoolyear_stat_lookup_production.pkl')

    # Load test / future data
    print("Loading data...", flush=True)

    # *** UPDATE THIS PATH ***
    raw = pd.read_csv('/Volumes/Untitled/smart-parking-ML-25-26/feature_list/TEST_01MAY2025-TO-06NOV2025_cyclic_1-model-small.csv')

    # Apply time features (stat lookup applied per-sub-model inside ensemble_predict)
    raw = add_time_features(raw)
    raw = raw[~((raw['Timestamp'].dt.month == 2) & (raw['Timestamp'].dt.day == 1))]
    raw = raw[raw['Zone'].isin(ZONE_INFO.keys())].reset_index(drop=True)

    has_ground_truth = 'Current Availability' in raw.columns

    # X_test keeps Timestamp and Zone for routing and spatial step
    # stat lookup is applied inside ensemble_predict per sub-model
    X_test = raw.drop(columns=['Current Availability'], errors='ignore')

    # Base ensemble prediction
    print("\n=== Ensemble Prediction ===", flush=True)
    t0 = time.time()
    y_pred = ensemble_predict(
        X_test, events_model, summer_model, school_model,
        events_lookup, summer_lookup, school_lookup
    )
    base_time = time.time() - t0

    results = pd.DataFrame({
        'Timestamp':      raw['Timestamp'].values,
        'Zone':           raw['Zone'].values,
        'Base_Predicted': y_pred
    })

    if has_ground_truth:
        results['Actual'] = raw['Current Availability'].values
        print_scores("Base Ensemble (Production LightGBM)",
                     results['Actual'], results['Base_Predicted'], base_time)

    # Spatial layer
    print("=== Spatial Adjustment ===", flush=True)
    t1 = time.time()
    final = apply_spatial_model(results, alpha=0.05, power=2, congestion_threshold=0.90)
    spatial_time = time.time() - t1

    final['Base_Predicted']          = final['Base_Predicted'].round().astype(int)
    final['Spatially_Adjusted_Pred'] = final['Spatially_Adjusted_Pred'].round().astype(int)

    if has_ground_truth:
        print_scores("Spatially Adjusted Ensemble",
                     final['Actual'], final['Spatially_Adjusted_Pred'], spatial_time)

    final.to_csv("final_predictions_newSY_summer.csv", index=False)
    print(f"\nTotal time: {base_time + spatial_time:.2f}s")
    print("Saved: final_predictions_newSY_summer.csv")


if __name__ == "__main__":
    run_pipeline()
