from sklearn.neighbors import KNeighborsClassifier as SklearnKNN
from ..base_model import BaseModel
from ..model_evaluation import ModelEvaluator
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import pickle
import os

class KNNClassifier(BaseModel):
    def __init__(self):
        super().__init__()
        # Create a pipeline with imputer, scaling, and KNN
        self.pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler()),
            ('knn', SklearnKNN(
                n_neighbors=5,
                weights='distance',
                metric='euclidean',
                n_jobs=-1,
                algorithm='kd_tree'
            ))
        ])
        self.metrics = None
        
    def train(self, X_train, y_train):
        """Train the KNN model"""
        try:
            print(f"Training KNN with input shapes - X: {X_train.shape}, y: {y_train.shape}")
            self.pipeline.fit(X_train, y_train)
            return self
        except Exception as e:
            print(f"KNN training error: {str(e)}")
            raise e

    def predict(self, X):
        """Predict using the pipeline"""
        try:
            return self.pipeline.predict(X)
        except Exception as e:
            print(f"KNN prediction error: {str(e)}")
            raise e

    def predict_proba(self, X):
        """Get probability predictions using the pipeline"""
        try:
            return self.pipeline.predict_proba(X)
        except Exception as e:
            print(f"KNN probability prediction error: {str(e)}")
            raise e

    def get_params(self):
        """Get model parameters"""
        return self.pipeline.named_steps['knn'].get_params()

    def evaluate(self, y_true, y_pred):
        """Evaluate model performance and store metrics"""
        try:
            # Calculate metrics using ModelEvaluator
            metrics = ModelEvaluator.evaluate_classification(y_true, y_pred)
            
            # Store metrics in the instance
            self.metrics = {
                'accuracy': float(metrics['accuracy']),
                'precision': float(metrics['precision']),
                'recall': float(metrics['recall']),
                'f1': float(metrics['f1']),
                'confusion_matrix': metrics['confusion_matrix'],
                'classification_report': metrics['classification_report']
            }
            
            print(f"KNN metrics calculated: {self.metrics}")  # Debug print
            return self.metrics
            
        except Exception as e:
            print(f"Error in KNN evaluation: {str(e)}")
            self.metrics = None
            raise e

    def get_metrics(self):
        """Get stored metrics"""
        return self.metrics
        
    def save_model(self, filepath):
        """Save the trained model and metrics to a file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if not hasattr(self, 'pipeline') or not self.pipeline:
                raise ValueError("No trained model to save")
                
            if not self.metrics:
                print("Warning: No metrics available when saving model")
                self.metrics = {
                    'accuracy': 0.0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1': 0.0
                }
            
            model_data = {
                'pipeline': self.pipeline,
                'metrics': self.metrics
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"Model and metrics saved successfully to {filepath}")
            return True
            
        except Exception as e:
            print(f"Error saving model: {str(e)}")
            return False
