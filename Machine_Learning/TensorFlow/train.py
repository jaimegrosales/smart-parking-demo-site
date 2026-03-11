import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, root_mean_squared_error
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import matplotlib.pyplot as plt

# Example dataset
parking_data = pd.read_csv("../generate_data/parking_data_feature_L6.csv", header=0)

# Split the data into features (X) and labels (y)
X = parking_data.drop(columns=['Current Availability']) 
y = parking_data['Current Availability']    

# Split dataset into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define the model
model = models.Sequential()
model.add(layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)))
model.add(layers.Dense(64, activation='relu'))
model.add(layers.Dense(32, activation='relu'))
model.add(layers.Dense(1, activation='sigmoid'))  # For binary classification

# Compile the model
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), 
              loss='binary_crossentropy', metrics=['accuracy'])

# Implement EarlyStopping callback
early_stopping = EarlyStopping(
    monitor='val_loss',  # you can monitor 'val_accuracy' as well
    patience=3,          # number of epochs with no improvement after which training will be stopped
    restore_best_weights=True  # restore model weights from the epoch with the best performance
)

# Define learning rate reduction
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3)

# Train the model with learning rate scheduler
history = model.fit(X_train, y_train,
                    epochs=100,
                    batch_size=32,
                    validation_split=0.2,
                    callbacks=[early_stopping, lr_scheduler])

# Evaluate the model
test_loss, test_acc = model.evaluate(X_test, y_test)
y_pred = model.predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
rmse = np.sqrt(root_mean_squared_error(y_test, y_pred))
print(f"Root Mean Squared Error: {rmse}")
print(f"Test Accuracy: {test_acc}")
print(f"Test Loss: {test_loss}")

# # Plot training history
# plt.plot(history.history['accuracy'])
# plt.plot(history.history['val_accuracy'])
# plt.title('Model accuracy')
# plt.ylabel('Accuracy')
# plt.xlabel('Epoch')
# plt.legend(['Train', 'Validation'], loc='upper left')
# plt.show()

# plt.plot(history.history['loss'])
# plt.plot(history.history['val_loss'])
# plt.title('Model loss')
# plt.ylabel('Loss')
# plt.xlabel('Epoch')
# plt.legend(['Train', 'Validation'], loc='upper left')
# plt.show()
