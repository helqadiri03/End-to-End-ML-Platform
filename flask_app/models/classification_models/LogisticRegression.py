from sklearn.linear_model import LogisticRegression as SklearnLogisticRegression
from ..base_model import BaseModel
from ..model_evaluation import ModelEvaluator
from sklearn.preprocessing import StandardScaler
import numpy as np

class LogisticRegressionClassifier(BaseModel):
    def __init__(self):
        super().__init__()
        self.scaler = StandardScaler()
        self.model = SklearnLogisticRegression(
            C=1.0,
            max_iter=1000,
            solver='lbfgs',
            multi_class='multinomial',
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        self.metrics = None

    def train(self, X_train, y_train):
        """Train the Logistic Regression model with scaled features"""
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X_train)
            
            # Train model
            print(f"Training Logistic Regression with input shapes - X: {X_scaled.shape}, y: {y_train.shape}")
            self.model.fit(X_scaled, y_train)
            return self
        except Exception as e:
            print(f"Logistic Regression training error: {str(e)}")
            raise e

    def predict(self, X):
        """Predict using scaled features"""
        try:
            X_scaled = self.scaler.transform(X)
            return self.model.predict(X_scaled)
        except Exception as e:
            print(f"Logistic Regression prediction error: {str(e)}")
            raise e

    def predict_proba(self, X):
        """Get probability predictions using scaled features"""
        try:
            X_scaled = self.scaler.transform(X)
            return self.model.predict_proba(X_scaled)
        except Exception as e:
            print(f"Logistic Regression probability prediction error: {str(e)}")
            raise e

    def get_params(self):
        """Get model parameters"""
        return self.model.get_params()
    
    def evaluate(self, y_true, y_pred):
        """Evaluate model performance"""
        self.metrics = ModelEvaluator.evaluate_classification(y_true, y_pred)
        return self.metrics