from sklearn.cluster import KMeans as SKLearnKMeans
from .base_clustering import BaseClusteringModel
import numpy as np

class KMeansCluster(BaseClusteringModel):
    def __init__(self, n_clusters=3):
        super().__init__()
        self.n_clusters = n_clusters
        self.model = None  # Will be initialized after finding K
        
    def find_k(self, X, k_range=range(2, 10)):
        """Find a good K using simple elbow detection"""
        inertias = []
        
        # Calculate inertia for each k
        for k in k_range:
            kmeans = SKLearnKMeans(n_clusters=k, random_state=42)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
        
        # Calculate percentage changes
        changes = []
        for i in range(1, len(inertias)):
            change = (inertias[i-1] - inertias[i]) / inertias[i-1] * 100
            changes.append(change)
        
        # Find first point where change becomes small
        threshold = 30  # 30% change threshold
        for i, change in enumerate(changes):
            if change < threshold:
                chosen_k = k_range[i + 1]  # +1 because changes array is one shorter
                print(f"Changes in inertia: {[f'{x:.1f}%' for x in changes]}")
                print(f"Choosing k={chosen_k} (change={change:.1f}%)")
                return chosen_k
        
        # If no clear elbow found, return default
        return 3
        
    def train(self, X):
        # Find good K value
        self.n_clusters = self.find_k(X)
        print(f"Training with {self.n_clusters} clusters")
        
        # Initialize and train model
        self.model = SKLearnKMeans(n_clusters=self.n_clusters, random_state=42)
        self.model.fit(X)
        self.X = X
        return self
        
    def predict(self, X):
        return self.model.predict(X) 