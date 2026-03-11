"""
Events Sub-Model — LightGBM Production Version
===============================================
Improvements for unseen-data prediction:
  1. Temporal 80/20 split for honest scoring
  2. Second 100%-trained model saved for deployment
  3. Statistical lookup features: zone+hour+dow mean/std from training data
  4. New time features: minute, day_of_year_sin/cos, week_of_year_sin/cos
  5. LightGBM + 100-trial Optuna search
  6. Event columns KEPT — they define event rows and are known ahead of time

OUTPUTS:
  best_events_lgbm_eval.pkl            — trained on 80%, for scoring
  best_events_lgbm_production.pkl      — trained on 100%, for deployment
  events_stat_lookup.pkl               — lookup table (needed at inference time)
  events_stat_lookup_production.pkl    — full-data lookup for deployment
"""

import pandas as pd
import numpy as np
import joblib
import time
import warnings
import optuna
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    explained_variance_score, mean_absolute_percentage_error
)
import lightgbm as lgb

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

ZONE_CAPACITIES = {
    29: 31,   31: 8,    33: 13,   35: 12,   37: 17,   38: 17,
    22: 1462, 13: 451,  19: 630,  4:  389,  3:  599,  42: 599,
    30: 2,    32: 4,    34: 2,    36: 3,    28: 4,    39: 4,
    27: 87,   40: 13,   6:  55,   12: 570,  2:  177
}

EVENT_COLUMNS = [
    'Ash Wednesday', 'Commencement', 'Easter Sunday', 'Exam Week',
    'Fall Break', 'Family Weekend', 'Home Football Game',
    'Home Football Game (Homecoming)', 'Labor Day',
    'Martin Luther King Jr. Day', 'Spring Break',
    "St. Patrick&#39;s Day", 'Thanksgiving Break', 'Winter Break'
]


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


def build_stat_lookup(df):
    lookup = (
        df.groupby(['Zone', 'hour', 'Day of Week'])['Current Availability']
        .agg(hist_mean='mean', hist_std='std')
        .reset_index()
    )
    lookup['hist_std'] = lookup['hist_std'].fillna(0)
    return lookup


def apply_stat_lookup(df, lookup):
    df = df.merge(lookup, on=['Zone', 'hour', 'Day of Week'], how='left')
    df['hist_mean'] = df['hist_mean'].fillna(df['hist_mean'].median())
    df['hist_std']  = df['hist_std'].fillna(0)
    return df


# ---------------------------------------------------------------------------
# Load & prepare
# ---------------------------------------------------------------------------
print("Reading CSV...", flush=True)

# *** UPDATE THIS PATH ***
data = pd.read_csv(
    "/Volumes/Untitled/smart-parking-ML-25-26/ensemble_ML/events_model/TO-19AUG2025_events_data.csv"
)

data = add_time_features(data)

# Keep only event rows (at least one event flag active)
event_mask = data[EVENT_COLUMNS].sum(axis=1) > 0
data = data[event_mask].reset_index(drop=True)
print(f"Event rows: {len(data):,}", flush=True)

# ---------------------------------------------------------------------------
# Temporal 80/20 split
# ---------------------------------------------------------------------------
split_idx = int(len(data) * 0.8)
train_df  = data.iloc[:split_idx].copy()
test_df   = data.iloc[split_idx:].copy()
print(f"Train: {len(train_df):,}  |  Test: {len(test_df):,}", flush=True)

stat_lookup = build_stat_lookup(train_df)
joblib.dump(stat_lookup, "events_stat_lookup.pkl")

train_df = apply_stat_lookup(train_df, stat_lookup)
test_df  = apply_stat_lookup(test_df,  stat_lookup)

DROP = ['Current Availability', 'Timestamp']
X_train, y_train = train_df.drop(columns=DROP, errors='ignore'), train_df['Current Availability']
X_test,  y_test  = test_df.drop(columns=DROP,  errors='ignore'), test_df['Current Availability']

print(f"Feature columns ({len(X_train.columns)}): {list(X_train.columns)}", flush=True)

# ---------------------------------------------------------------------------
# Optuna search
# ---------------------------------------------------------------------------
def objective(trial):
    params = {
        'objective':         'regression',
        'metric':            'mae',
        'verbosity':         -1,
        'boosting_type':     'gbdt',
        'n_estimators':      trial.suggest_int('n_estimators', 300, 1500),
        'learning_rate':     trial.suggest_float('learning_rate', 0.005, 0.15, log=True),
        'num_leaves':        trial.suggest_int('num_leaves', 20, 300),
        'max_depth':         trial.suggest_int('max_depth', 4, 16),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
        'subsample':         trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree':  trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha':         trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda':        trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        'n_jobs': -1, 'random_state': 42,
    }
    m = lgb.LGBMRegressor(**params)
    m.fit(X_train, y_train,
          eval_set=[(X_test, y_test)],
          callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)])
    return mean_absolute_error(y_test, m.predict(X_test))

print("Optuna search (100 trials)...", flush=True)
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100, show_progress_bar=True)
best_params = study.best_params
best_params.update({'objective': 'regression', 'metric': 'mae',
                    'verbosity': -1, 'n_jobs': -1, 'random_state': 42})
print(f"Best MAE: {study.best_value:.4f} | Params: {best_params}\n", flush=True)

# ---------------------------------------------------------------------------
# Eval model — 80%
# ---------------------------------------------------------------------------
print("Training eval model...", flush=True)
t0 = time.time()
eval_m = lgb.LGBMRegressor(**best_params)
eval_m.fit(X_train, y_train,
           eval_set=[(X_test, y_test)],
           callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)])
elapsed = time.time() - t0
print_scores("Events LightGBM — Eval (80/20 Temporal)", y_test, eval_m.predict(X_test), elapsed)
joblib.dump(eval_m, "best_events_lgbm_eval.pkl")
print("Saved: best_events_lgbm_eval.pkl", flush=True)

# ---------------------------------------------------------------------------
# Production model — 100% data
# ---------------------------------------------------------------------------
print("Training production model (100% data)...", flush=True)
full_lookup = build_stat_lookup(data)
joblib.dump(full_lookup, "events_stat_lookup_production.pkl")
full_data = apply_stat_lookup(data.copy(), full_lookup)
X_full = full_data.drop(columns=DROP, errors='ignore')
y_full = full_data['Current Availability']

t0 = time.time()
prod_m = lgb.LGBMRegressor(**best_params)
prod_m.fit(X_full, y_full, callbacks=[lgb.log_evaluation(-1)])
print(f"Production model trained in {time.time()-t0:.2f}s")
joblib.dump(prod_m, "best_events_lgbm_production.pkl")
print("Saved: best_events_lgbm_production.pkl", flush=True)
print("Saved: events_stat_lookup_production.pkl")
print("\nDeploy: best_events_lgbm_production.pkl + events_stat_lookup_production.pkl")
