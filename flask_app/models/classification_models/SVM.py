from sklearn.svm import LinearSVC, SVC
from ..base_model import BaseModel
from ..model_evaluation import ModelEvaluator
from sklearn.preprocessing import StandardScaler
import numpy as np

class SVMClassifier(BaseModel):
    def __init__(self):
        super().__init__()
        self.scaler = StandardScaler()
        self.model = None
        self.use_linear = False
        self.metrics = None

    def train(self, X_train, y_train):
        """Train the SVM model with scaled features and automatic model selection"""
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X_train)
            n_samples, n_features = X_scaled.shape
            
            # Choose between LinearSVC (faster) and SVC (more accurate) based on dataset size
            if n_samples * n_features > 100000:  # Large dataset
                print("Using LinearSVC for faster training on large dataset")
                self.use_linear = True
                self.model = LinearSVC(
                    C=1.0,
                    class_weight='balanced',
                    dual=False,  # Faster for n_samples > n_features
                    max_iter=1000,
                    random_state=42
                )
            else:
                print("Using SVC for better accuracy on smaller dataset")
                self.model = SVC(
                    C=1.0,
                    kernel='rbf',
                    gamma='scale',
                    probability=True,
                    class_weight='balanced',
                    random_state=42,
                    cache_size=2000,  # Increased cache size
                    max_iter=1000
                )
            
            # Train model
            print(f"Training SVM with input shapes - X: {X_scaled.shape}, y: {y_train.shape}")
            self.model.fit(X_scaled, y_train)
            return self
        except Exception as e:
            print(f"SVM training error: {str(e)}")
            raise e

    def predict(self, X):
        """Predict using scaled features"""
        try:
            X_scaled = self.scaler.transform(X)
            return self.model.predict(X_scaled)
        except Exception as e:
            print(f"SVM prediction error: {str(e)}")
            raise e

    def predict_proba(self, X):
        """Get probability predictions using scaled features"""
        try:
            X_scaled = self.scaler.transform(X)
            if self.use_linear:
                # For LinearSVC, convert decision function to probabilities
                decision_values = self.model.decision_function(X_scaled)
                if len(decision_values.shape) == 1:
                    # Binary classification
                    proba = 1 / (1 + np.exp(-decision_values))
                    return np.vstack((1 - proba, proba)).T
                else:
                    # Multiclass classification
                    exp_decision = np.exp(decision_values)
                    return exp_decision / exp_decision.sum(axis=1, keepdims=True)
            else:
                return self.model.predict_proba(X_scaled)
        except Exception as e:
            print(f"SVM probability prediction error: {str(e)}")
            raise e

    def get_params(self):
        """Get model parameters"""
        return self.model.get_params() if self.model else {}
    
    def evaluate(self, y_true, y_pred):
        """Evaluate model performance"""
        self.metrics = ModelEvaluator.evaluate_classification(y_true, y_pred)
        return self.metrics