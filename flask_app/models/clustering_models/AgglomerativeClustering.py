from sklearn.cluster import AgglomerativeClustering as SKLearnAgglomerativeClustering
from .base_clustering import BaseClusteringModel
import numpy as np
from sklearn.metrics import pairwise_distances

class AgglomerativeCluster(BaseClusteringModel):
    def __init__(self, n_clusters=3):
        super().__init__()
        self.n_clusters = n_clusters
        self.model = None  # Will be initialized after finding K
        
    def find_k(self, X, k_range=range(2, 10)):
        """Find a good K using simple elbow detection"""
        distances = []
        
        # Calculate average distance within clusters for each k
        for k in k_range:
            model = SKLearnAgglomerativeClustering(n_clusters=k)
            labels = model.fit_predict(X)
            
            # Calculate average distance within clusters
            total_dist = 0
            for i in range(k):
                cluster_points = X[labels == i]
                if len(cluster_points) > 1:
                    dists = pairwise_distances(cluster_points)
                    total_dist += dists.sum() / (2 * len(cluster_points))
            
            distances.append(total_dist)
        
        # Calculate percentage changes
        changes = []
        for i in range(1, len(distances)):
            change = (distances[i-1] - distances[i]) / distances[i-1] * 100
            changes.append(change)
        
        # Find first point where change becomes small
        threshold = 25  # 25% change threshold
        for i, change in enumerate(changes):
            if change < threshold:
                chosen_k = k_range[i + 1]
                print(f"Changes in distances: {[f'{x:.1f}%' for x in changes]}")
                print(f"Choosing k={chosen_k} (change={change:.1f}%)")
                return chosen_k
        
        # If no clear elbow found, return default
        return 3
        
    def train(self, X):
        # Find good K value
        self.n_clusters = self.find_k(X)
        print(f"Training with {self.n_clusters} clusters")
        
        # Initialize and train model
        self.model = SKLearnAgglomerativeClustering(n_clusters=self.n_clusters)
        self.model.fit(X)
        self.X = X
        return self
        
    def predict(self, X):
        # AgglomerativeClustering doesn't have predict method
        # We need to fit again for new data
        self.model.fit(X)
        return self.model.labels_ 