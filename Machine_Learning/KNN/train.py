import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, accuracy_score, root_mean_squared_error
import matplotlib.pyplot as plt

parking_data = pd.read_csv("../generate_data/parking_data_feature_L6.csv", header=0)

# Split the data into features (X) and labels (y)
X = parking_data.drop(columns=['Current Availability']) 
y = parking_data['Current Availability']                  

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the KNN classifier
knn = KNeighborsClassifier(n_neighbors=29)  # Change n_neighbors as needed

# Fit the model on the training data
knn.fit(X_train, y_train)

# Make predictions on the test set
y_pred = knn.predict(X_test)

# Evaluate the model
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
rmse = np.sqrt(root_mean_squared_error(y_test, y_pred))
print(f"Root Mean Squared Error: {rmse}")

# Optionally, plot accuracy for different K values
k_values = range(1, 21)
accuracies = []

# for k in k_values:
#     knn = KNeighborsClassifier(n_neighbors=k)
#     scores = cross_val_score(knn, X, y, cv=5)  # 5-fold cross-validation
#     accuracies.append(scores.mean())

# # Plotting the accuracy for different K values
# plt.figure(figsize=(10, 6))
# plt.plot(k_values, accuracies, marker='o')
# plt.title('KNN: Varying Number of Neighbors')
# plt.xlabel('Number of Neighbors (K)')
# plt.ylabel('Cross-Validated Accuracy')
# plt.xticks(k_values)
# plt.grid()
# plt.show()
