from sklearn.cluster import DBSCAN as SKLearnDBSCAN
from .base_clustering import BaseClusteringModel

class DBSCANCluster(BaseClusteringModel):
    def __init__(self, eps=0.5, min_samples=5):
        super().__init__()
        self.eps = eps
        self.min_samples = min_samples
        self.model = SKLearnDBSCAN(eps=eps, min_samples=min_samples)
        
    def train(self, X):
        self.X = X  # Store the training data
        self.model.fit(X)
        return self
        
    def predict(self, X):
        return self.model.fit_predict(X) 