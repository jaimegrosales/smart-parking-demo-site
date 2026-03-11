# Run all Here
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, TimeSeriesSplit
from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score, explained_variance_score, mean_absolute_percentage_error
)
import joblib
import time

# For KNN
from sklearn.neighbors import KNeighborsRegressor

# For ELNET
from sklearn.linear_model import ElasticNet

# For RF Regressor
from sklearn.ensemble import RandomForestRegressor

def adjusted_mape(y_true, y_pred):
    # Avoid division by zero by replacing zero values in y_true with a small value
    nonzero_indices = y_true != 0  # Only consider values where y_true is non-zero
    y_true_nonzero = y_true[nonzero_indices]
    y_pred_nonzero = y_pred[nonzero_indices]

    # Calculate the MAPE using sklearn's implementation
    mape_value = mean_absolute_percentage_error(y_true_nonzero, y_pred_nonzero) * 100  # Convert to percentage
    
    # Return the MAPE as a percentage
    return mape_value
    
def eval(y_test, y_pred):
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = adjusted_mape(y_test, y_pred)
    r_squared = r2_score(y_test, y_pred)
    ev = explained_variance_score(y_test, y_pred)

    print(f"\tRMSE: {rmse:.4f}")
    print(f"\tMAE: {mae:.4f}")
    print(f"\tMAPE: {mape:.2f}%")
    print(f"\tr2: {r_squared:.4f}")
    print(f"\tev: {ev:.4f}", flush=True)
    return
    
def graph_model(y_test, y_pred, file):
    plt.figure(figsize=(8,6))
    plt.scatter(y_test, y_pred, alpha=0.7, color='blue')
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], '--', color='red')
    plt.xlabel("Actual Values")
    plt.ylabel("Predicted Values")
    plt.title("Actual vs. Predicted Values")
    plt.savefig(file)

print("Reading .csv", flush=True)
# Load cyclic class meeting times
full_cyclic = pd.read_csv("cleaned_pd.csv", header=0)
semi_cyclic = pd.read_csv("cleaned_pd_semi.csv", header=0)
full_class = pd.read_csv("cleaned_pd_class.csv", header=0)

# FULL CYCLIC
full_cyclic_X = full_cyclic.drop(columns=['Current Availability'])
full_cyclic_y = full_cyclic['Current Availability']

fcyclic_X_train, fcyclic_X_test, fcyclic_y_train, fcyclic_y_test = train_test_split(full_cyclic_X, full_cyclic_y, test_size=0.2, random_state=42)

# SEMI CYCLIC
semi_cyclic_X = semi_cyclic.drop(columns=['Current Availability'])
semi_cyclic_y = semi_cyclic['Current Availability']

scyclic_X_train, scyclic_X_test, scyclic_y_train, scyclic_y_test = train_test_split(semi_cyclic_X, semi_cyclic_y, test_size=0.2, random_state=42)

# FULL CYCLIC CLASS TIMES
full_class_X = full_class.drop(columns=['Current Availability'])
full_class_y = full_class['Current Availability']

fclass_X_train, fclass_X_test, fclass_y_train, fclass_y_test = train_test_split(full_class_X, full_class_y, test_size=0.2, random_state=42)


# Dictionary for Models for creating REC Graph
models = {}

# REC Graph to Compare


# KNN Training
print("\nKNN", flush=True)

# Train Semi
knn_semi = KNeighborsRegressor(
    n_neighbors=29,
    algorithm='ball_tree',
    n_jobs=-1
)
print("\tTraining Semi Cyclic", flush=True)
knn_semi.fit(scyclic_X_train, scyclic_y_train)
print("\tPredicting Semi Cyclic", flush=True)
knn_semi_y_pred = knn_semi.predict(scyclic_X_test)
joblib.dump(knn_semi, "knn/knn_semi.pkl")
print("\tModel saved", flush=True)

eval(scyclic_y_test, knn_semi_y_pred)
graph_model(scyclic_y_test, knn_semi_y_pred, "knn/knn_semi.png")
# Save Model to Dict
models["KNN (Semi Cyclic No Class Meeting Time)"] = ("knn_semi", scyclic_y_test, knn_semi_y_pred)

# Train Full Cyclic Class
knn_fclass = KNeighborsRegressor(
    n_neighbors=29,
    algorithm='ball_tree',
    n_jobs=-1
)
print("\tTraining Full Cyclic Class", flush=True)
knn_fclass.fit(fclass_X_train, fclass_y_train)
print("\tPredicting Full Cyclic Class", flush=True)
knn_fclass_y_pred = knn_fclass.predict(fclass_X_test)
joblib.dump(knn_fclass, "knn/knn_fclass.pkl")
print("\tModel saved", flush=True)

eval(fclass_y_test, knn_fclass_y_pred)
graph_model(fclass_y_test, knn_fclass_y_pred, "knn/knn_fclass.png")
# Save Model to Dict
models["KNN (Full Cyclic Class Meeting Time)"] = ("knn_fclass", fclass_y_test, knn_fclass_y_pred)

# Load Full Cyclic
knn_fcyclic = joblib.load("knn/best_knn.pkl")
print("\tPredicting Full Cyclic", flush=True)
knn_fcyclic_y_pred = knn_fcyclic.predict(fcyclic_X_test)
joblib.dump(knn_fcyclic, "knn/knn_fcyclic.pkl")
print("\tModel saved", flush=True)

eval(fcyclic_y_test, knn_fcyclic_y_pred)
graph_model(fcyclic_y_test, knn_fcyclic_y_pred, "knn/knn_fcyclic.png")
# Save Model to Dict
models["KNN (Full Cyclic No Class Meeting Time)"] = ("knn_fcyclic", fcyclic_y_test, knn_fcyclic_y_pred)

# REC Graph to Compare



# RFR Training
print("\nRFR", flush=True)

# Train Semi
rfr_semi = RandomForestRegressor(
    max_depth=15,
    min_samples_leaf=1,
    min_samples_split=2,
    n_estimators=150,
    n_jobs=-1
)
print("\tTraining Semi Cyclic", flush=True)
rfr_semi.fit(scyclic_X_train, scyclic_y_train)
print("\tPredicting Semi Cyclic", flush=True)
rfr_semi_y_pred = rfr_semi.predict(scyclic_X_test)
joblib.dump(rfr_semi, "rfr/rfr_semi.pkl")
print("\tModel saved", flush=True)

eval(scyclic_y_test, rfr_semi_y_pred)
graph_model(scyclic_y_test, rfr_semi_y_pred, "rfr/rfr_semi.png")
# Save Model to Dict
models["RFR (Semi Cyclic No Class Meeting Time)"] = ("rfr_semi", scyclic_y_test, rfr_semi_y_pred)

# Train Full Cyclic Class
rfr_fclass = RandomForestRegressor(
    max_depth=15,
    min_samples_leaf=1,
    min_samples_split=2,
    n_estimators=150,
    n_jobs=-1
)
print("\tTraining Full Cyclic Class", flush=True)
rfr_fclass.fit(fclass_X_train, fclass_y_train)
print("\tPredicting Full Cyclic Class", flush=True)
rfr_fclass_y_pred = rfr_fclass.predict(fclass_X_test)
joblib.dump(rfr_fclass, "rfr/rfr_fclass.pkl")
print("\tModel saved", flush=True)

eval(fclass_y_test, rfr_fclass_y_pred)
graph_model(fclass_y_test, rfr_fclass_y_pred, "rfr/rfr_fclass.png")
# Save Model to Dict
models["RFR (Full Cyclic Class Meeting Time)"] = ("rfr_fclass", fclass_y_test, rfr_fclass_y_pred)

# Load Full Cyclic
rfr_fcyclic = joblib.load("rfr/best_rfr.pkl")
print("\tPredicting Full Cyclic", flush=True)
rfr_fcyclic_y_pred = rfr_fcyclic.predict(fcyclic_X_test)
joblib.dump(rfr_fcyclic, "rfr/rfr_fcyclic.pkl")
print("\tModel saved", flush=True)

eval(fcyclic_y_test, rfr_fcyclic_y_pred)
graph_model(fcyclic_y_test, rfr_fcyclic_y_pred, "rfr/rfr_fcyclic.png")
# Save Model to Dict
models["RFR (Full Cyclic No Class Meeting Time)"] = ("rfr_fcyclic", fcyclic_y_test, rfr_fcyclic_y_pred)

# REC Graph to Compare

# FULL EVAL

# Create combined REC graph with all and filter to only show up to 20 spot error

def plot_rec_curve(models):
    model_colors = {
        "rfr": "red",
        "knn": "black",
        "elnet": "green"
    }
    
    feature_styles = {
        "fcyclic": "-",
        "semi": "-.-",
        "fclass": ":"
    }
    
    plt.figure(figsize=(8, 6))
    
    for i, (model_name, (model, y_test, y_pred)) in enumerate(models.items()):
        errors = np.abs(y_pred - y_test)
        tolerance_values = np.linspace(0, errors.max(), 100)
        percentages = [
            np.mean(errors <= tolerance) for tolerance in tolerance_values
        ]
        line_style = feature_styles.get(model.split("_")[1])
        color = model_colors.get(model.split("_")[0])
        plt.plot(
            tolerance_values,
            percentages,
            label=model_name,
            linestyle=line_style,
            color=color,
            markersize=5,
            linewith=2
        )
    
    plt.xlin(0, 20)
    
    plt.xlabel("Error Tolerance")
    plt.ylabel("Percentage of Predictions Within Tolerance")
    plt.title("Regression Error Characteristic (REC) Curve for ML Models Predictability")
    plt.legend()
    plt.grid(True)
    plt.savefig("compare.png")
    
plot_rec_curve(models)

