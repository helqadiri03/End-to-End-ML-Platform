from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFromModel
import numpy as np
from ..base_model import BaseModel

class XGBoostRegressionModel(BaseModel):
    def __init__(self):
        super().__init__(task='regression')
        self.target_scaler = StandardScaler()
        self.model = Pipeline([
            ('robust_scaler', RobustScaler()),
            ('feature_select', SelectFromModel(XGBRegressor(n_estimators=50), max_features=4)),
            ('scaler', StandardScaler()),
            ('xgboost', XGBRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=1,
                tree_method='hist',
                max_bin=256,
                reg_alpha=0,
                reg_lambda=1,
                random_state=42,
                n_jobs=-1
            ))
        ])
        self.model_name = "XGBoost Regression"

    def train(self, X_train, y_train):
        """Train the XGBoost model with optimizations"""
        try:
            X_train = np.asarray(X_train)
            y_train = np.asarray(y_train)
            print(f"Training data statistics:")
            print(f"X_train shape: {X_train.shape}")
            print(f"y_train shape: {y_train.shape}")
            print(f"y_train range: [{np.min(y_train)}, {np.max(y_train)}]")
            print(f"y_train mean: {np.mean(y_train)}, std: {np.std(y_train)}")
            if np.any(~np.isfinite(X_train)):
                print("Warning: X_train contains infinite or NaN values")
                X_train = np.nan_to_num(X_train, nan=0, posinf=0, neginf=0)
            if np.any(~np.isfinite(y_train)):
                print("Warning: y_train contains infinite or NaN values")
                y_train = np.nan_to_num(y_train, nan=0, posinf=0, neginf=0)
            if X_train.shape[0] > 10000:
                indices = np.random.choice(X_train.shape[0], 10000, replace=False)
                X_train = X_train[indices]
                y_train = y_train[indices]
            self.model.fit(X_train, y_train)
            try:
                xgb_model = self.model.named_steps['xgboost']
                self.feature_importances_ = xgb_model.feature_importances_
                print("\nTop feature importances:")
                for i in np.argsort(self.feature_importances_)[-5:]:
                    print(f"Feature {i}: {self.feature_importances_[i]:.4f}")
            except Exception as e:
                print(f"Could not get feature importances: {str(e)}")
            train_predictions = self.model.predict(X_train)
            print("\nTraining predictions statistics:")
            print(f"Range: [{np.min(train_predictions)}, {np.max(train_predictions)}]")
            print(f"Mean: {np.mean(train_predictions)}, Std: {np.std(train_predictions)}")
            from sklearn.metrics import r2_score
            train_r2 = r2_score(y_train, train_predictions)
            print(f"Training R² score: {train_r2}")
            return True
        except Exception as e:
            print(f"Error training XGBoost model: {str(e)}")
            return False

    def predict(self, X):
        """Make predictions with the model"""
        try:
            X = np.asarray(X)
            if np.any(~np.isfinite(X)):
                print("Warning: X contains infinite or NaN values")
                X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
            predictions = self.model.predict(X)
            print(f"Prediction statistics:")
            print(f"Range: [{np.min(predictions)}, {np.max(predictions)}]")
            print(f"Mean: {np.mean(predictions)}, Std: {np.std(predictions)}")
            return predictions
        except Exception as e:
            print(f"Error in prediction: {str(e)}")
            return None

    def get_feature_importances(self):
        """Return feature importances if model is trained"""
        if hasattr(self, 'feature_importances_'):
            return self.feature_importances_
        return None