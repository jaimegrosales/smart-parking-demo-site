"""
Prediction Error Diagnostic
============================
Loads final_predictions.csv and breaks down errors by:
  - Zone (individual garage)
  - Permit type (Commuter, Accessible, EV, Faculty)
  - Day type (Weekday, Weekend)
  - Hour of day (heatmap-style)
  - Month

Helps identify exactly where the remaining MAE/MAPE is coming from.

INPUT:  final_predictions.csv  (output from run_ensemble_spatial.py)
OUTPUT: prints a full breakdown + saves diagnostic_report.csv
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import warnings

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Zone metadata
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_mape(y_true, y_pred):
    mask = np.array(y_true) != 0
    if mask.sum() == 0:
        return np.nan
    return mean_absolute_percentage_error(
        np.array(y_true)[mask], np.array(y_pred)[mask]
    ) * 100


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def compute_metrics(group, actual_col, pred_col):
    y_true = group[actual_col].values
    y_pred = group[pred_col].values
    if len(y_true) < 2:
        return None
    return {
        'N':    len(y_true),
        'MAE':  round(mean_absolute_error(y_true, y_pred), 3),
        'RMSE': round(np.sqrt(mean_squared_error(y_true, y_pred)), 3),
        'MAPE': round(safe_mape(y_true, y_pred), 2),
        'R2':   round(r2_score(y_true, y_pred), 4),
    }


# ---------------------------------------------------------------------------
# Load predictions
# ---------------------------------------------------------------------------
print("Loading final_predictions.csv...", flush=True)

# *** UPDATE THIS PATH if your CSV is not in the same directory ***
df = pd.read_csv('/Users/michaelcraig/Desktop/lgbm_files/final_predictions.csv')

# Check required columns exist
required = {'Timestamp', 'Zone', 'Actual', 'Base_Predicted', 'Spatially_Adjusted_Pred'}
missing  = required - set(df.columns)
if missing:
    raise ValueError(f"Missing columns in final_predictions.csv: {missing}\n"
                     "Make sure your test CSV had a 'Current Availability' column "
                     "when you ran run_ensemble_spatial.py.")

df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df['hour']      = df['Timestamp'].dt.hour
df['month']     = df['Timestamp'].dt.month
df['dow']       = df['Timestamp'].dt.dayofweek   # 0=Mon, 6=Sun
df['is_weekend']= (df['dow'] >= 5).astype(int)
df['day_type']  = df['is_weekend'].map({0: 'Weekday', 1: 'Weekend'})

# Attach zone metadata
df['deck']      = df['Zone'].map(lambda z: ZONE_INFO.get(z, {}).get('deck', 'Unknown'))
df['perm_type'] = df['Zone'].map(lambda z: ZONE_INFO.get(z, {}).get('type', 'Unknown'))
df['capacity']  = df['Zone'].map(lambda z: ZONE_INFO.get(z, {}).get('cap', np.nan))

ACTUAL = 'Actual'
PRED   = 'Spatially_Adjusted_Pred'
BASE   = 'Base_Predicted'

print(f"Loaded {len(df):,} rows covering {df['Timestamp'].min()} → {df['Timestamp'].max()}")

# ---------------------------------------------------------------------------
# SECTION 1 — Overall summary
# ---------------------------------------------------------------------------
section("1. OVERALL SUMMARY")
for label, pred_col in [("Base Ensemble", BASE), ("Spatially Adjusted", PRED)]:
    m = compute_metrics(df, ACTUAL, pred_col)
    print(f"\n  {label}:")
    print(f"    MAE:  {m['MAE']:.4f}  |  RMSE: {m['RMSE']:.4f}  |  MAPE: {m['MAPE']:.2f}%  |  R2: {m['R2']:.4f}")

# ---------------------------------------------------------------------------
# SECTION 2 — By permit type
# ---------------------------------------------------------------------------
section("2. BY PERMIT TYPE (Spatially Adjusted)")
perm_rows = []
for ptype, grp in df.groupby('perm_type'):
    m = compute_metrics(grp, ACTUAL, PRED)
    if m:
        m['Permit Type'] = ptype
        perm_rows.append(m)

perm_df = pd.DataFrame(perm_rows).set_index('Permit Type')[['N','MAE','RMSE','MAPE','R2']]
print(f"\n{perm_df.to_string()}")
print("\n  ← High MAPE in small zones (EV, Accessible) is expected due to tiny capacities.")
print("    Focus optimization efforts on Commuter and Faculty zones.")

# ---------------------------------------------------------------------------
# SECTION 3 — By zone (sorted by MAE descending)
# ---------------------------------------------------------------------------
section("3. BY ZONE (Spatially Adjusted, sorted by MAE)")
zone_rows = []
for zone, grp in df.groupby('Zone'):
    m = compute_metrics(grp, ACTUAL, PRED)
    if m:
        info = ZONE_INFO.get(zone, {})
        m['Zone']  = zone
        m['Deck']  = info.get('deck', '?')
        m['Type']  = info.get('type', '?')
        m['Cap']   = info.get('cap', '?')
        zone_rows.append(m)

zone_df = (pd.DataFrame(zone_rows)
           .set_index('Zone')
           .sort_values('MAE', ascending=False)
           [['Deck','Type','Cap','N','MAE','RMSE','MAPE','R2']])
print(f"\n{zone_df.to_string()}")

# ---------------------------------------------------------------------------
# SECTION 4 — By day type (Weekday vs Weekend)
# ---------------------------------------------------------------------------
section("4. BY DAY TYPE (Spatially Adjusted)")
for day, grp in df.groupby('day_type'):
    m = compute_metrics(grp, ACTUAL, PRED)
    print(f"\n  {day} ({m['N']:,} rows):")
    print(f"    MAE: {m['MAE']:.4f}  |  RMSE: {m['RMSE']:.4f}  |  MAPE: {m['MAPE']:.2f}%  |  R2: {m['R2']:.4f}")

# ---------------------------------------------------------------------------
# SECTION 5 — By hour of day (commuter zones only)
# ---------------------------------------------------------------------------
section("5. BY HOUR OF DAY — Commuter Zones Only (Spatially Adjusted)")
commuter_df = df[df['perm_type'] == 'Commuter']
hour_rows = []
for hour, grp in commuter_df.groupby('hour'):
    m = compute_metrics(grp, ACTUAL, PRED)
    if m:
        m['Hour'] = hour
        hour_rows.append(m)

hour_df = (pd.DataFrame(hour_rows)
           .set_index('Hour')
           [['N','MAE','RMSE','MAPE','R2']])
print(f"\n{hour_df.to_string()}")
print("\n  ← High MAE hours indicate when parking transitions quickly (arrival/departure rushes).")

# ---------------------------------------------------------------------------
# SECTION 6 — By month
# ---------------------------------------------------------------------------
section("6. BY MONTH (Spatially Adjusted)")
month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
               7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
month_rows = []
for month, grp in df.groupby('month'):
    m = compute_metrics(grp, ACTUAL, PRED)
    if m:
        m['Month'] = month_names.get(month, month)
        month_rows.append(m)

month_df = (pd.DataFrame(month_rows)
            .set_index('Month')
            [['N','MAE','RMSE','MAPE','R2']])
print(f"\n{month_df.to_string()}")

# ---------------------------------------------------------------------------
# SECTION 7 — Worst predicted individual zones (error concentration)
# ---------------------------------------------------------------------------
section("7. ERROR CONCENTRATION — Where is the MAE coming from?")
df['abs_error'] = (df[ACTUAL] - df[PRED]).abs()
total_mae_contribution = df.groupby('Zone')['abs_error'].mean()
total_error_share      = df.groupby('Zone')['abs_error'].sum()
total_error_sum        = total_error_share.sum()

conc_rows = []
for zone in total_mae_contribution.index:
    info = ZONE_INFO.get(zone, {})
    conc_rows.append({
        'Zone':       zone,
        'Deck':       info.get('deck', '?'),
        'Type':       info.get('type', '?'),
        'Cap':        info.get('cap', '?'),
        'Avg Error':  round(total_mae_contribution[zone], 3),
        'Error Share': f"{100 * total_error_share[zone] / total_error_sum:.1f}%"
    })

conc_df = (pd.DataFrame(conc_rows)
           .set_index('Zone')
           .sort_values('Avg Error', ascending=False))
print(f"\n{conc_df.to_string()}")
print("\n  ← 'Error Share' = what % of total absolute error this zone contributes.")
print("    Zones with high Error Share AND high capacity are your priority targets.")

# ---------------------------------------------------------------------------
# Save full report
# ---------------------------------------------------------------------------
zone_df.to_csv("diagnostic_by_zone.csv")
hour_df.to_csv("diagnostic_by_hour_commuter.csv")
month_df.to_csv("diagnostic_by_month.csv")
conc_df.to_csv("diagnostic_error_concentration.csv")

print(f"\n{'='*60}")
print("  Saved diagnostic CSVs:")
print("    diagnostic_by_zone.csv")
print("    diagnostic_by_hour_commuter.csv")
print("    diagnostic_by_month.csv")
print("    diagnostic_error_concentration.csv")
print(f"{'='*60}\n")