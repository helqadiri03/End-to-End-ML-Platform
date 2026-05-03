from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
import numpy as np
from joblib import parallel_backend, Parallel, delayed
from ..base_model import BaseModel


class RandomForestRegressionModel(BaseModel):
    def __init__(self):
        super().__init__(task='regression')

        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('feature_select', SelectFromModel(
                RandomForestRegressor(n_estimators=50, n_jobs=-1),
                max_features=4
            )),
            ('rf', RandomForestRegressor(
                n_estimators=100,
                max_depth=None,
                min_samples_split=5,
                min_samples_leaf=2,
                max_features='sqrt',
                bootstrap=True,
                oob_score=True,
                n_jobs=-1,
                random_state=42,
                warm_start=True,
                max_samples=0.8
            ))

        ])

        self.model_name = "Enhanced Random Forest Regression"


    def train(self, X_train, y_train):
        """Train the Random Forest model with parallel processing optimizations"""
        try:
            # Convert to numpy arrays and handle data preprocessing in parallel

            def preprocess_chunk(X_chunk, y_chunk):
                X_chunk = np.nan_to_num(X_chunk, nan=0, posinf=0, neginf=0)
                y_chunk = np.nan_to_num(y_chunk, nan=0, posinf=0, neginf=0)
                return X_chunk, y_chunk

            X_train = np.asarray(X_train)
            y_train = np.asarray(y_train).ravel()

            # Print input data statistics

            print(f"Training data statistics:")
            print(f"X_train shape: {X_train.shape}")
            print(f"y_train shape: {y_train.shape}")

            # Parallel preprocessing of data

            chunk_size = max(1000, len(X_train) // (Parallel(n_jobs=-1).n_jobs * 4))
            chunks = [(X_train[i:i+chunk_size], y_train[i:i+chunk_size])
                      for i in range(0, len(X_train), chunk_size)]

            with parallel_backend('threading', n_jobs=-1):
                processed_chunks = Parallel(n_jobs=-1)(
                    delayed(preprocess_chunk)(X_chunk, y_chunk)
                    for X_chunk, y_chunk in chunks
                )

            X_train = np.vstack([chunk[0] for chunk in processed_chunks])
            y_train = np.concatenate([chunk[1] for chunk in processed_chunks])

            print("Starting enhanced Random Forest training with parallel processing...")

            # Perform cross-validation with parallel processing

            with parallel_backend('threading', n_jobs=-1):
                cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='r2', n_jobs=-1)

                print(f"Cross-validation R² scores: {cv_scores}")
                print(f"Mean CV R² score: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")

                # Train the final model

                self.model.fit(X_train, y_train)

            # Get feature importances

            rf_model = self.model.named_steps['rf']

            self.feature_importances_ = rf_model.feature_importances_

            top_features = np.argsort(self.feature_importances_)[-10:][::-1]

            print("\nTop 10 feature importances:")
            for i in top_features:
                print(f"Feature {i}: {self.feature_importances_[i]:.4f}")

            # Calculate performance metrics

            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

            train_predictions = self.model.predict(X_train)

            train_r2 = r2_score(y_train, train_predictions)
            train_rmse = np.sqrt(mean_squared_error(y_train, train_predictions))
            train_mae = mean_absolute_error(y_train, train_predictions)

            print(f"\nTraining metrics:")
            print(f"R² score: {train_r2:.4f}")
            print(f"RMSE: {train_rmse:.4f}")
            print(f"MAE: {train_mae:.4f}")
            print(f"Out-of-bag score: {rf_model.oob_score_:.4f}")

            return True

        except Exception as e:

            print(f"Error training Random Forest model: {str(e)}")

            return False

    def predict(self, X):
        """Make predictions with parallel processing"""
        try:
            X = np.asarray(X)
            X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)

            with parallel_backend('threading', n_jobs=-1):
                predictions = self.model.predict(X)

            return predictions

        except Exception as e:

            print(f"Error making predictions: {str(e)}")

            return None

    def get_feature_importances(self):
        """Return feature importances if model is trained"""
        if hasattr(self, 'feature_importances_'):

            return self.feature_importances_

        return None

