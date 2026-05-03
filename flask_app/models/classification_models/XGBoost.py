from xgboost import XGBClassifier
from ..base_model import BaseModel
from ..model_evaluation import ModelEvaluator
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import train_test_split
import os
import pickle
import pandas as pd
import numpy as np

class XGBoostClassifier(BaseModel):
    def __init__(self):
        super().__init__()
        self.base_model = XGBClassifier(
            n_estimators=500,
            max_depth=5,
            learning_rate=0.1,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='auc'
        )
        
        # Create pipeline with feature selection
        self.model = Pipeline([
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler()),
            ('feature_selector', SelectFromModel(
                estimator=XGBClassifier(
                    n_estimators=100,
                    max_depth=3,
                    random_state=42,
                    eval_metric='auc'
                ),
                threshold='mean'
            )),
            ('xgb', self.base_model)
        ])
        
        self.metrics = None
        self.label_encoder = LabelEncoder()
        self.threshold = 0.5

    def train(self, X_train, y_train):
        """Train XGBoost with feature selection and threshold optimization"""
        try:
            print(f"Training XGBoost with input shapes - X: {X_train.shape}, y: {y_train.shape}")
            
            # Convert to numpy arrays if needed
            if isinstance(X_train, pd.DataFrame):
                X_train = X_train.values
            if isinstance(y_train, pd.Series):
                y_train = y_train.values
            
            # Encode target labels
            y_encoded = self.label_encoder.fit_transform(y_train)
            
            # Print class distribution
            unique, counts = np.unique(y_encoded, return_counts=True)
            print(f"Class distribution: {dict(zip(unique, counts))}")
            
            # Split for validation
            X_train_main, X_val, y_train_main, y_val = train_test_split(
                X_train, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
            )
            
            # Train the model with feature selection
            print("\nTraining model with feature selection...")
            
            # First apply preprocessing and feature selection
            X_train_processed = self.model.named_steps['imputer'].fit_transform(X_train_main)
            X_train_processed = self.model.named_steps['scaler'].fit_transform(X_train_processed)
            X_train_processed = self.model.named_steps['feature_selector'].fit_transform(X_train_processed, y_train_main)
            
            # Process validation data
            X_val_processed = self.model.named_steps['imputer'].transform(X_val)
            X_val_processed = self.model.named_steps['scaler'].transform(X_val_processed)
            X_val_processed = self.model.named_steps['feature_selector'].transform(X_val_processed)
            
            # Get selected features
            feature_selector = self.model.named_steps['feature_selector']
            n_selected = sum(feature_selector.get_support())
            print(f"\nSelected {n_selected} features")
            
            # Train the final model
            print("\nTraining final model...")
            self.base_model.fit(
                X_train_processed, 
                y_train_main,
                eval_set=[(X_val_processed, y_val)],
                verbose=True
            )
            
            # Find optimal threshold
            print("\nOptimizing decision threshold...")
            val_proba = self.base_model.predict_proba(X_val_processed)[:, 1]
            
            # Try different threshold ranges based on class distribution
            thresholds = np.linspace(0.3, 0.7, 21)  # More granular search around 0.5
            best_f1 = 0
            best_threshold = 0.5
            best_metrics = None
            
            print("\nThreshold optimization results:")
            for threshold in thresholds:
                y_pred = (val_proba >= threshold).astype(int)
                metrics = ModelEvaluator.evaluate_classification(y_val, y_pred)
                print(f"Threshold: {threshold:.2f}, "
                      f"F1: {metrics['f1']:.3f}, "
                      f"Precision: {metrics['precision']:.3f}, "
                      f"Recall: {metrics['recall']:.3f}")
                
                # Use F1 score for threshold selection
                if metrics['f1'] > best_f1:
                    best_f1 = metrics['f1']
                    best_threshold = threshold
                    best_metrics = metrics
            
            self.threshold = best_threshold
            print(f"\nSelected optimal threshold: {self.threshold:.3f}")
            print(f"Best validation metrics:")
            print(f"F1: {best_metrics['f1']:.3f}")
            print(f"Precision: {best_metrics['precision']:.3f}")
            print(f"Recall: {best_metrics['recall']:.3f}")
            print(f"Accuracy: {best_metrics['accuracy']:.3f}")
            
            # Store the validation metrics
            self.metrics = best_metrics
            
            return self
            
        except Exception as e:
            print(f"XGBoost training error: {str(e)}")
            raise e

    def evaluate(self, y_true, y_pred):
        """Evaluate model performance and return validation metrics"""
        try:
            # Convert predictions back to original labels if needed
            if hasattr(self.label_encoder, 'classes_'):
                if not isinstance(y_true, np.ndarray):
                    y_true = np.array(y_true)
                if not isinstance(y_pred, np.ndarray):
                    y_pred = np.array(y_pred)
                
                # Only transform if they're not already transformed
                if y_true.dtype != np.int64:
                    y_true = self.label_encoder.transform(y_true)
                if y_pred.dtype != np.int64:
                    y_pred = self.label_encoder.transform(y_pred)
            
            # Return the stored validation metrics if available
            if hasattr(self, 'metrics') and self.metrics is not None:
                return self.metrics
            
            # Calculate metrics using ModelEvaluator
            metrics = ModelEvaluator.evaluate_classification(y_true, y_pred)
            
            # Store metrics in the instance
            self.metrics = {
                'accuracy': float(metrics['accuracy']),
                'precision': float(metrics['precision']),
                'recall': float(metrics['recall']),
                'f1': float(metrics['f1'])
            }
            
            return self.metrics
            
        except Exception as e:
            print(f"Error in XGBoost evaluation: {str(e)}")
            self.metrics = None
            raise e

    def predict(self, X):
        """Make predictions using optimal threshold"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
            
            # Convert to numpy array if needed
            if isinstance(X, pd.DataFrame):
                X = X.values
            
            # Preprocess the data
            X_processed = self.model.named_steps['imputer'].transform(X)
            X_processed = self.model.named_steps['scaler'].transform(X_processed)
            X_processed = self.model.named_steps['feature_selector'].transform(X_processed)
            
            # Get probability predictions
            probas = self.base_model.predict_proba(X_processed)[:, 1]
            
            # Apply optimal threshold
            predictions = (probas >= self.threshold).astype(int)
            
            # Inverse transform labels if needed
            if hasattr(self.label_encoder, 'classes_'):
                predictions = self.label_encoder.inverse_transform(predictions)
            
            return predictions
            
        except Exception as e:
            print(f"XGBoost prediction error: {str(e)}")
            raise e

    def save_model(self, filepath):
        """Save both base and calibrated models"""
        try:
            model_data = {
                'base_model': self.base_model,
                'model': self.model,
                'label_encoder': self.label_encoder,
                'threshold': self.threshold,
                'metrics': self.metrics
            }
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
        except Exception as e:
            print(f"Error saving model: {str(e)}")
            raise e

    def load_model(self, filepath):
        """Load both base and calibrated models"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            self.base_model = model_data['base_model']
            self.model = model_data['model']
            self.label_encoder = model_data['label_encoder']
            self.threshold = model_data.get('threshold', 0.5)
            self.metrics = model_data.get('metrics', None)
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise e