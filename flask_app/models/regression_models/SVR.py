from sklearn.svm import SVR
from sklearn.linear_model import Lasso
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFromModel
import numpy as np
from ..base_model import BaseModel

class SVRModel(BaseModel):
    def __init__(self):
        super().__init__(task='regression')
        
        # Use MinMaxScaler instead of StandardScaler for better SVR performance
        self.model = Pipeline([
            ('scaler', RobustScaler()),  # Single scaler is enough
            ('svr', SVR(
                kernel='linear',  # Changed to linear kernel for housing data
                C=100.0,  # Much higher C for less regularization
                epsilon=0.1,
                gamma='auto',
                cache_size=1000,
                max_iter=-1,  # No limit on iterations
                tol=1e-3
            ))
        ])
        self.model_name = "Support Vector Regression"
        
    def train(self, X_train, y_train):
        """Train the SVR model with optimizations"""
        try:
            # Convert to numpy arrays
            X_train = np.asarray(X_train)
            y_train = np.asarray(y_train)
            
            # Print input data statistics
            print(f"Training data statistics:")
            print(f"X_train shape: {X_train.shape}")
            print(f"y_train shape: {y_train.shape}")
            print(f"y_train range: [{np.min(y_train)}, {np.max(y_train)}]")
            print(f"y_train mean: {np.mean(y_train)}, std: {np.std(y_train)}")
            
            # Ensure y_train is 1D
            y_train = y_train.ravel()
            
            # Check for infinite or NaN values
            if np.any(~np.isfinite(X_train)):
                print("Warning: X_train contains infinite or NaN values")
                X_train = np.nan_to_num(X_train, nan=0, posinf=0, neginf=0)
            
            if np.any(~np.isfinite(y_train)):
                print("Warning: y_train contains infinite or NaN values")
                y_train = np.nan_to_num(y_train, nan=0, posinf=0, neginf=0)
            
            # Subsample large datasets
            if X_train.shape[0] > 10000:  # Increased sample size
                indices = np.random.choice(X_train.shape[0], 10000, replace=False)
                X_train = X_train[indices]
                y_train = y_train[indices]
                print(f"Subsampled training data to {X_train.shape[0]} samples")
            
            # Train the model
            print("Starting SVR training...")
            self.model.fit(X_train, y_train)
            print("SVR training completed")
            
            # Make training predictions for sanity check
            train_predictions = self.model.predict(X_train)
            print("\nTraining predictions statistics:")
            print(f"Range: [{np.min(train_predictions)}, {np.max(train_predictions)}]")
            print(f"Mean: {np.mean(train_predictions)}, Std: {np.std(train_predictions)}")
            
            # Calculate and print training R² score
            from sklearn.metrics import r2_score
            train_r2 = r2_score(y_train, train_predictions)
            print(f"Training R² score: {train_r2:.4f}")
            
            return True
            
        except Exception as e:
            print(f"Error training SVR model: {str(e)}")
            return False
    
    def predict(self, X):
        """Make predictions with the model"""
        try:
            X = np.asarray(X)
            
            # Check for infinite or NaN values
            if np.any(~np.isfinite(X)):
                print("Warning: X contains infinite or NaN values")
                X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
            
            print("Making SVR predictions...")
            predictions = self.model.predict(X)
            print("Predictions completed")
            
            # Print prediction statistics
            print(f"Prediction statistics:")
            print(f"Range: [{np.min(predictions)}, {np.max(predictions)}]")
            print(f"Mean: {np.mean(predictions)}, Std: {np.std(predictions)}")
            
            return predictions
            
        except Exception as e:
            print(f"Error in SVR prediction: {str(e)}")
            return None