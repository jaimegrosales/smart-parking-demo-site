import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import root_mean_squared_error
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
from keras.callbacks import History, EarlyStopping

# Load the dataset
dataset = pd.read_csv('09-25-2024-3.csv')

# Preprocess the data

# Feature Engineering: Extract useful time-based features from Timestamp
dataset['Timestamp'] = pd.to_datetime(dataset['Timestamp'])  # Ensure Timestamp is in datetime format
dataset['hour'] = dataset['Timestamp'].dt.hour
dataset['day_of_week'] = dataset['Timestamp'].dt.dayofweek
dataset['day_of_month'] = dataset['Timestamp'].dt.day
dataset['month'] = dataset['Timestamp'].dt.month

# Split features and target
X = dataset.drop(columns=['Current Availability'])
y = dataset['Current Availability']

# Split the dataset into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Define preprocessing pipeline for numeric and categorical features
numeric_features = ['Availability Ratio', 'hour', 'day_of_week', 'day_of_month', 'month']
numeric_transformer = Pipeline(steps=[
    ('scaler', StandardScaler())
])

categorical_features = ['Day of Week', 'During Standard Meeting Time?', 'Standard Meeting Time Window']
categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# Preprocess the data
X_train_transformed = preprocessor.fit_transform(X_train)
X_test_transformed = preprocessor.transform(X_test)

# Convert the sparse matrix to a dense matrix before reshaping
X_train_dense = X_train_transformed.toarray()
X_test_dense = X_test_transformed.toarray()

# Add a third dimension for timesteps (assuming one timestep per instance)
X_train_reshaped = X_train_dense.reshape((X_train_dense.shape[0], 1, X_train_dense.shape[1]))
X_test_reshaped = X_test_dense.reshape((X_test_dense.shape[0], 1, X_test_dense.shape[1]))

# Get the number of features after preprocessing
num_features = X_train_reshaped.shape[2]

# Define the LSTM model
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(1, num_features)),
    LSTM(32, return_sequences=False),
    Dense(32, activation='relu'),
    Dropout(0.2),  # Adding dropout for regularization
    Dense(1)
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Define EarlyStopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# Train the model
history = History()
history = model.fit(X_train_reshaped, y_train, epochs=50, batch_size=32, validation_split=0.2, callbacks=[history, early_stopping])

# Evaluate the model
train_loss = history.history['loss']
val_loss = history.history['val_loss']
test_loss = model.evaluate(X_test_reshaped, y_test)

# Predictions
y_train_pred = model.predict(X_train_reshaped)
y_test_pred = model.predict(X_test_reshaped)

# Calculate RMSE
train_rmse = np.sqrt(root_mean_squared_error(y_train, y_train_pred))
test_rmse = np.sqrt(root_mean_squared_error(y_test, y_test_pred))

# Plot actual vs predicted for train and test sets with text annotations
plt.figure(figsize=(10, 6))
plt.scatter(X_train['Timestamp'], y_train, color='blue', label='Actual Train', s=10)
plt.scatter(X_train['Timestamp'], y_train_pred, color='red', label='Predicted Train', s=10)
plt.scatter(X_test['Timestamp'], y_test, color='green', label='Actual Test', s=10)
plt.scatter(X_test['Timestamp'], y_test_pred, color='orange', label='Predicted Test', s=10)

plt.xlabel('Timestamp')
plt.ylabel('Current Availability')
plt.ylim(0, 100)

# Add text annotations beside the title
title_text = 'Actual vs Predicted Availability\n'
title_text += f'Test Loss: {test_loss:.4f}   Train RMSE: {train_rmse:.4f}   Test RMSE: {test_rmse:.4f}'

plt.title(title_text, loc='left')

# Print metrics
print("Train Loss:", train_loss)
print("Validation Loss:", val_loss)
print("Test Loss:", test_loss)
print("Train RMSE:", train_rmse)
print("Test RMSE:", test_rmse)

plt.legend()
plt.show()
