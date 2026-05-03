from sklearn.ensemble import RandomForestClassifier as SklearnRandomForest
from ..base_model import BaseModel
from ..model_evaluation import ModelEvaluator
from sklearn.preprocessing import StandardScaler
import numpy as np

class RandomForestClassifier(BaseModel):
    def __init__(self):
        super().__init__()
        self.scaler = StandardScaler()
        self.model = SklearnRandomForest(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            bootstrap=True,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        self.metrics = None

    def train(self, X_train, y_train):
        """Train the Random Forest model with scaled features"""
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X_train)
            
            # Train model
            print(f"Training Random Forest with input shapes - X: {X_scaled.shape}, y: {y_train.shape}")
            self.model.fit(X_scaled, y_train)
            return self
        except Exception as e:
            print(f"Random Forest training error: {str(e)}")
            raise e

    def predict(self, X):
        """Predict using scaled features"""
        try:
            X_scaled = self.scaler.transform(X)
            return self.model.predict(X_scaled)
        except Exception as e:
            print(f"Random Forest prediction error: {str(e)}")
            raise e

    def get_params(self):
        """Get model parameters"""
        return self.model.get_params()
    
    def evaluate(self, y_true, y_pred):
        """Evaluate model performance"""
        self.metrics = ModelEvaluator.evaluate_classification(y_true, y_pred)
        return self.metrics