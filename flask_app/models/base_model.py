from abc import ABC, abstractmethod
import pickle
import numpy as np
from .model_evaluation import ModelEvaluator

class BaseModel(ABC):
    def __init__(self, task='classification'):
        self.model = None
        self.model_name = None
        self.task = task
        self.metrics = {}
        self.target_scaler = None
        
    @abstractmethod
    def train(self, X_train, y_train):
        """Train the model"""
        pass
    
    @abstractmethod
    def predict(self, X):
        """Make predictions"""
        pass
    
    def evaluate(self, y_true, y_pred):
        """Evaluate the model"""
        try:
            # Convert pandas Series to numpy arrays if needed
            if hasattr(y_true, 'to_numpy'):
                y_true = y_true.to_numpy()
            if hasattr(y_pred, 'to_numpy'):
                y_pred = y_pred.to_numpy()
                
            # Print shapes for debugging
            print(f"Initial shapes - y_true: {y_true.shape}, y_pred: {y_pred.shape}")
            
            # Ensure arrays are 1D
            y_true = y_true.ravel() if hasattr(y_true, 'ravel') else y_true
            y_pred = y_pred.ravel() if hasattr(y_pred, 'ravel') else y_pred
            
            print(f"Final shapes - y_true: {y_true.shape}, y_pred: {y_pred.shape}")
            print(f"Value ranges - y_true: [{y_true.min()}, {y_true.max()}], y_pred: [{y_pred.min()}, {y_pred.max()}]")
            
            # Evaluate using appropriate metrics
            evaluator = ModelEvaluator()
            self.metrics = evaluator.evaluate(y_true, y_pred, task=self.task)
            
            if self.task == 'regression':
                print(f"Regression metrics:")
                for metric, value in self.metrics.items():
                    print(f"{metric}: {value}")
            
            return self.metrics
            
        except Exception as e:
            print(f"Error in model evaluation: {str(e)}")
            print(f"Input types - y_true: {type(y_true)}, y_pred: {type(y_pred)}")
            if hasattr(y_true, 'shape'):
                print(f"y_true shape: {y_true.shape}")
            if hasattr(y_pred, 'shape'):
                print(f"y_pred shape: {y_pred.shape}")
            return {}
    
    def save_model(self, filepath):
        """Save model, metrics, and target scaler to file"""
        if self.model is None:
            raise ValueError("No model to save")
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'metrics': self.metrics,
                'model_name': self.model_name,
                'target_scaler': self.target_scaler
            }, f)
        
    def load_model(self, path):
        """Load model, metrics, and target scaler from file"""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
            if isinstance(model_data, dict):
                self.model = model_data.get('model')
                self.metrics = model_data.get('metrics', {})
                self.model_name = model_data.get('model_name')
                self.target_scaler = model_data.get('target_scaler')
            else:
                self.model = model_data