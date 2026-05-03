from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import LassoCV
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_regression
import numpy as np
from joblib import parallel_backend
from ..base_model import BaseModel

class PolynomialRegressionModel(BaseModel):
    def __init__(self):
        super().__init__(task='regression')
        
        # Optimized pipeline with careful feature selection
        self.model = Pipeline([
            ('scaler1', StandardScaler()),
            ('poly', PolynomialFeatures(
                degree=2,
                include_bias=False
            )),
            ('select_features', SelectKBest(
                score_func=f_regression,
                k=20  # Select top 20 features
            )),
            ('scaler2', StandardScaler()),
            ('lasso', LassoCV(
                eps=1e-3,
                n_alphas=100,
                cv=5,
                max_iter=2000,
                tol=1e-4,
                n_jobs=-1,
                random_state=42
            ))
        ])
        self.model_name = "Stable Polynomial Regression"
        
    def train(self, X_train, y_train):
        """Train with careful preprocessing and feature selection"""
        try:
            X_train = np.asarray(X_train)
            y_train = np.asarray(y_train).ravel()
            
            # Handle missing values
            X_train = np.nan_to_num(X_train, copy=False)
            y_train = np.nan_to_num(y_train, copy=False)
            
            # Remove outliers using IQR
            Q1 = np.percentile(y_train, 25)
            Q3 = np.percentile(y_train, 75)
            IQR = Q3 - Q1
            mask = (y_train >= Q1 - 1.5 * IQR) & (y_train <= Q3 + 1.5 * IQR)
            X_train = X_train[mask]
            y_train = y_train[mask]
            
            print(f"Training shape after preprocessing: {X_train.shape}")
            
            # Train with parallel processing
            with parallel_backend('threading', n_jobs=-1):
                self.model.fit(X_train, y_train)
            
            # Calculate metrics
            train_pred = self.model.predict(X_train)
            r2 = 1 - np.sum((y_train - train_pred) ** 2) / np.sum((y_train - np.mean(y_train)) ** 2)
            mse = np.mean((y_train - train_pred) ** 2)
            rmse = np.sqrt(mse)
            
            print(f"Training R²: {r2:.4f}")
            print(f"Training RMSE: {rmse:.4f}")
            
            return True
            
        except Exception as e:
            print(f"Training error: {str(e)}")
            return False
    
    def predict(self, X):
        """Careful prediction with preprocessing"""
        try:
            X = np.nan_to_num(np.asarray(X), copy=False)
            return self.model.predict(X)
                
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return None