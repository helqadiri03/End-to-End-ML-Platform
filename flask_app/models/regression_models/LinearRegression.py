from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.linear_model import LassoCV, RidgeCV, ElasticNetCV
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sklearn.feature_selection import SelectKBest, f_regression
import numpy as np
from joblib import parallel_backend
from ..base_model import BaseModel

class LinearRegressionModel(BaseModel):
    def __init__(self):
        super().__init__(task='regression')
        
        # Create a more robust pipeline with feature selection and multiple models
        self.model = Pipeline([
            ('scaler', StandardScaler()),  # Standardize features
            ('feature_selection', SelectKBest(score_func=f_regression, k='all')),  # Select best features
            ('regressor', ElasticNetCV(
                l1_ratio=[.1, .5, .7, .9, .95, .99, 1],
                eps=1e-3,
                n_alphas=100,
                max_iter=2000,
                tol=1e-4,
                cv=5,
                n_jobs=-1  # Use all CPUs
            ))
        ])
        self.model_name = "Enhanced Linear Regression"
        
    def train(self, X_train, y_train):
        """Train the enhanced linear regression model"""
        try:
            # Convert to numpy arrays
            X_train = np.asarray(X_train)
            y_train = np.asarray(y_train)
            
            # Print input data statistics
            print(f"Training data statistics:")
            print(f"X_train shape: {X_train.shape}")
            print(f"y_train shape: {y_train.shape}")
            
            # Ensure y_train is 1D
            y_train = y_train.ravel()
            
            # Handle infinite/NaN values
            X_train = np.nan_to_num(X_train, nan=0, posinf=0, neginf=0)
            y_train = np.nan_to_num(y_train, nan=0, posinf=0, neginf=0)
            
            # Remove outliers using IQR method
            Q1 = np.percentile(y_train, 25)
            Q3 = np.percentile(y_train, 75)
            IQR = Q3 - Q1
            outlier_mask = (y_train >= Q1 - 1.5 * IQR) & (y_train <= Q3 + 1.5 * IQR)
            X_train = X_train[outlier_mask]
            y_train = y_train[outlier_mask]
            
            print("Starting enhanced linear regression training...")
            
            # Use parallel backend for training
            with parallel_backend('threading', n_jobs=-1):
                # Perform cross-validation first
                cv_scores = cross_val_score(self.model, X_train, y_train, 
                                         cv=5, scoring='r2', n_jobs=-1)
                print(f"Cross-validation R² scores: {cv_scores}")
                print(f"Mean CV R² score: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
                
                # Train the final model
                self.model.fit(X_train, y_train)
            
            # Get feature importance scores
            feature_scores = None
            if hasattr(self.model.named_steps['feature_selection'], 'scores_'):
                feature_scores = self.model.named_steps['feature_selection'].scores_
                print("\nTop feature importance scores:")
                for i, score in enumerate(feature_scores):
                    print(f"Feature {i}: {score:.4f}")
            
            # Make training predictions
            train_predictions = self.model.predict(X_train)
            
            # Calculate metrics
            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
            train_r2 = r2_score(y_train, train_predictions)
            train_rmse = np.sqrt(mean_squared_error(y_train, train_predictions))
            train_mae = mean_absolute_error(y_train, train_predictions)
            
            print(f"\nTraining metrics:")
            print(f"R² score: {train_r2:.4f}")
            print(f"RMSE: {train_rmse:.4f}")
            print(f"MAE: {train_mae:.4f}")
            
            return True
            
        except Exception as e:
            print(f"Error training enhanced linear regression model: {str(e)}")
            return False
    
    def predict(self, X):
        """Make predictions with the model"""
        try:
            X = np.asarray(X)
            X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
            
            with parallel_backend('threading', n_jobs=-1):
                predictions = self.model.predict(X)
            
            return predictions
            
        except Exception as e:
            print(f"Error making predictions: {str(e)}")
            return None
