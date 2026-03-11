import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)
import joblib
from joblib import Parallel, delayed

def adjusted_mape(y_true, y_pred):
    nonzero_indices = y_true != 0  
    y_true_nonzero = y_true[nonzero_indices]
    y_pred_nonzero = y_pred[nonzero_indices]
    return mean_absolute_percentage_error(y_true_nonzero, y_pred_nonzero) * 100  

def eval(y_test, y_pred):
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = adjusted_mape(y_test, y_pred)
    r_squared = r2_score(y_test, y_pred)
    ev = explained_variance_score(y_test, y_pred)
    
    n = len(y_test)  
    p = y_test.shape[1] if len(y_test.shape) > 1 else 1  
    adjusted_r2 = 1 - ((1 - r_squared) * (n - 1) / (n - p - 1))

    print(f"\tRMSE: {rmse:.4f}")
    print(f"\tMAE: {mae:.4f}")
    print(f"\tMAPE: {mape:.2f}%")
    print(f"\tr2: {r_squared:.4f}")
    print(f"\tadjusted r2: {adjusted_r2:.4f}")
    print(f"\tev: {ev:.4f}", flush=True)

# Load models
events_model = joblib.load('../events_models/best_events_knn.pkl')
summer_model = joblib.load('../summer_models/best_summer_knn.pkl')
school_model = joblib.load('../schoolYear_models/best_school_knn.pkl')

# Load data
events_data = pd.read_csv('../events_models/events_data.csv').drop(columns=['Zone Name'])
summer_data = pd.read_csv('../summer_models/summer_data.csv').drop(columns=['Zone Name'])
school_data = pd.read_csv('../schoolYear_models/schoolYear_data.csv').drop(columns=['Zone Name'])

# Split data
def split_data(data):
    X = data.drop(columns=['Current Availability'])
    y = data['Current Availability']
    return train_test_split(X, y, test_size=0.2, random_state=42)

events_X_train, events_X_test, events_y_train, events_y_test = split_data(events_data)
school_X_train, school_X_test, school_y_train, school_y_test = split_data(school_data)
summer_X_train, summer_X_test, summer_y_train, summer_y_test = split_data(summer_data)

X_test = pd.concat([events_X_test, school_X_test, summer_X_test], axis=0, ignore_index=True)
y_test = pd.concat([events_y_test, school_y_test, summer_y_test], axis=0, ignore_index=True)

# Event Columns
event_columns = ['Ash Wednesday', 'Commencement', 'Easter Sunday', 'Exam Week', 'Fall Break', 'Family Weekend',
                'Home Football Game', 'Home Football Game (Homecoming)', 'Independence Day', 'Juneteenth',
                'Labor Day', 'Martin Luther King Jr. Day', 'Memorial Day', 'Spring Break', 'St. Patrick&#39;s Day',
                'Thanksgiving Break', 'Winter Break']

def classify_rows(X_test):
    event_mask = X_test[event_columns].sum(axis=1) > 0
    summer_mask = X_test['month'].isin([6, 7, 8]) & ~event_mask
    school_mask = ~event_mask & ~summer_mask

    return event_mask, summer_mask, school_mask


def ensemble_predict(X_test):
    pred = []
    event_mask, summer_mask, school_mask = classify_rows(X_test)

    X_event = X_test[event_mask]
    X_summer = X_test[summer_mask].drop(columns=event_columns, errors='ignore')
    X_school = X_test[school_mask].drop(columns=event_columns, errors='ignore')
    
    pred_event = events_model.predict(X_event)
    pred_school = school_model.predict(X_school)
    pred_summer = summer_model.predict(X_summer)

    pred = np.concatenate([pred_event, pred_school, pred_summer]) 
    return pred

# Make predictions
testing_pred = ensemble_predict(X_test)
eval(y_test, testing_pred)

# Save results
testing_pred = pd.DataFrame(testing_pred, columns=["Predicted"])
results = pd.concat([y_test.reset_index(drop=True), testing_pred], axis=1)

results.to_csv('testing_results.csv', index=False)


