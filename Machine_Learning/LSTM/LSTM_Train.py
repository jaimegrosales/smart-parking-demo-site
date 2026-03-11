import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import root_mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from keras.callbacks import History, EarlyStopping

# Load the dataset
dataset = pd.read_csv('09-25-2024-3.csv')

# Preprocess the data
# Convert timestamp to datetime
dataset['Timestamp'] = pd.to_datetime(dataset['Timestamp'])

# Split features and target
X = dataset.drop(columns=['Current Availability'])
y = dataset['Current Availability']

# Split the dataset into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Define preprocessing pipeline for numeric and categorical features
numeric_features = ['Availability Ratio']
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


# Get the number of features after preprocessing
num_features = preprocessor.fit_transform(X_train).shape[1]

# Define the model
model = Sequential([
    Dense(64, activation='relu', input_shape=(num_features,)),  # Updated input_shape
    Dense(32, activation='relu'),
    Dense(1)
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Define EarlyStopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# Train the model
history = History()
model.fit(preprocessor.fit_transform(X_train), y_train, epochs=50, batch_size=32, validation_split=0.2, callbacks=[history, early_stopping])

# Evaluate the model
train_loss = history.history['loss']
val_loss = history.history['val_loss']
test_loss = model.evaluate(preprocessor.transform(X_test), y_test)

# Predictions
y_train_pred = model.predict(preprocessor.transform(X_train))
y_test_pred = model.predict(preprocessor.transform(X_test))

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



print("Train Loss:", train_loss)
print("Validation Loss:", val_loss)
print("Test Loss:", test_loss)
print("Train RMSE:", train_rmse)
print("Test RMSE:", test_rmse)

plt.legend()
plt.show()