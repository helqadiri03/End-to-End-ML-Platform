from sklearn.naive_bayes import GaussianNB, BernoulliNB
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from ..base_model import BaseModel
from ..model_evaluation import ModelEvaluator
import numpy as np
import pandas as pd

class NaiveBayesClassifier(BaseModel):
    def __init__(self):
        super().__init__()
        # Using BernoulliNB for binary features and GaussianNB for continuous
        self.model = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', MinMaxScaler()),  # MinMaxScaler works better for Naive Bayes
            ('nb', BernoulliNB(alpha=1.0))  # Using BernoulliNB for better binary classification
        ])
        self.metrics = None

    def train(self, X_train, y_train):
        """Train the Naive Bayes model with proper preprocessing"""
        try:
            print(f"Training Naive Bayes with input shapes - X: {X_train.shape}, y: {y_train.shape}")
            
            # Convert inputs to numpy arrays if needed
            if isinstance(X_train, pd.DataFrame):
                X_train = X_train.values
            if isinstance(y_train, pd.Series):
                y_train = y_train.values
            
            # Print class distribution
            unique, counts = np.unique(y_train, return_counts=True)
            class_dist = dict(zip(unique, counts))
            print(f"Class distribution: {class_dist}")
            
            # Calculate class weights
            n_samples = len(y_train)
            n_classes = len(unique)
            class_weights = {c: n_samples / (n_classes * count) for c, count in class_dist.items()}
            print(f"Class weights: {class_weights}")
            
            # Fit the pipeline
            self.model.fit(X_train, y_train)
            
            # Calculate optimal threshold using training data
            if len(unique) == 2:
                proba = self.model.predict_proba(X_train)
                thresholds = np.linspace(0.3, 0.7, 9)  # Try different thresholds
                best_f1 = 0
                best_threshold = 0.5
                
                for threshold in thresholds:
                    y_pred = (proba[:, 1] >= threshold).astype(int)
                    metrics = ModelEvaluator.evaluate_classification(y_train, y_pred)
                    if metrics['f1'] > best_f1:
                        best_f1 = metrics['f1']
                        best_threshold = threshold
                
                self.threshold = best_threshold
                print(f"Optimal decision threshold: {self.threshold:.3f} (F1: {best_f1:.3f})")
            
            print("Naive Bayes training completed successfully")
            return self
            
        except Exception as e:
            print(f"Error in Naive Bayes training: {str(e)}")
            raise e
            
    def predict(self, X):
        """Make predictions using the pipeline"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
            
            # Convert to numpy array if needed
            if isinstance(X, pd.DataFrame):
                X = X.values
            
            # Get probability predictions
            probas = self.model.predict_proba(X)
            
            # Apply optimal threshold for binary classification
            if hasattr(self, 'threshold') and self.threshold is not None:
                predictions = (probas[:, 1] >= self.threshold).astype(int)
            else:
                predictions = self.model.predict(X)
            
            return predictions
            
        except Exception as e:
            print(f"Error in Naive Bayes prediction: {str(e)}")
            raise e
    
    def get_params(self):
        """Get model parameters"""
        return self.model.named_steps['nb'].get_params()
    
    def evaluate(self, y_true, y_pred):
        """Evaluate model performance"""
        self.metrics = ModelEvaluator.evaluate_classification(y_true, y_pred)
        return self.metrics