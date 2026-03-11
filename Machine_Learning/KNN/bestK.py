import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
import matplotlib.pyplot as plt

# Load your dataset
df = pd.read_csv('../generate_data/parking_data_feature_L6.csv')

X = df.drop(columns=['Current Availability'])
y = df['Current Availability']

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Test different values of k
k_values = range(1, 31)
mean_scores = []

for k in k_values:
    knn = KNeighborsClassifier(n_neighbors=k)
    scores = cross_val_score(knn, X_train, y_train, cv=5)  # 5-fold cross-validation
    mean_scores.append(scores.mean())

# Plot the results
plt.plot(k_values, mean_scores)
plt.xlabel('Number of Neighbors K')
plt.ylabel('Mean Accuracy')
plt.title('KNN Hyperparameter Tuning')
plt.show()
