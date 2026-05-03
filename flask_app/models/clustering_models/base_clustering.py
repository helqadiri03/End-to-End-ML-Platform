
from abc import ABC, abstractmethod
import pickle
import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

class BaseClusteringModel(ABC):
    def __init__(self):
        self.model = None
        self.metrics = {}
        self.X = None  # Store the training data
        
    @abstractmethod
    def train(self, X):
        """
        Train the clustering model
        
        Args:
            X: Input features
        """
        self.X = X  # Store the training data
        pass
    
    @abstractmethod
    def predict(self, X):
        pass
    
    def evaluate(self, X):
        """Evaluate clustering performance"""
        if self.model is None:
            raise ValueError("Model must be trained before evaluation")
        
        try:
            labels = self.model.labels_ if hasattr(self.model, 'labels_') else self.model.predict(X)
            
            # Store data and labels for visualization
            self.X = X
            self.labels = labels
            
            # Calculate metrics
            metrics = {
                'silhouette': float(silhouette_score(X, labels)),
                'calinski_harabasz': float(calinski_harabasz_score(X, labels)),
                'davies_bouldin': float(davies_bouldin_score(X, labels)),
                'n_clusters': len(np.unique(labels[labels != -1])),
                'cluster_sizes': [int(sum(labels == i)) for i in range(len(np.unique(labels)))],
                'noise_points': int(sum(labels == -1)) if -1 in labels else 0
            }
            
            # Store metrics in the instance
            self.metrics = metrics
            return metrics
        except Exception as e:
            print(f"Error in clustering evaluation: {str(e)}")
            return None
    
    def save_model(self, filepath):
        """Save the model to a file"""
        try:
            # Create visualization before saving
            if hasattr(self, 'X') and hasattr(self, 'labels'):
                from app import create_cluster_visualization
                visualization = create_cluster_visualization(self.X, self.labels, self.__class__.__name__)
                if visualization:
                    self.metrics['visualization'] = visualization

            with open(filepath, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'metrics': self.metrics,
                    'cluster_info': {
                        'cluster_data': self.X,
                        'labels': self.labels
                    }
                }, f)
        except Exception as e:
            print(f"Error saving model: {str(e)}")
            raise
