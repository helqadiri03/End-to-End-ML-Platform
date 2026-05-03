from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    confusion_matrix, classification_report,
    silhouette_score, calinski_harabasz_score, davies_bouldin_score
)
import numpy as np
from typing import Dict, Any, Union, Optional
import logging
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelEvaluator:
    @staticmethod
    def evaluate_classification(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Evaluate classification model performance.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            Dictionary containing classification metrics
        """
        try:
            # Convert inputs to numpy arrays if they aren't already
            y_true = np.asarray(y_true)
            y_pred = np.asarray(y_pred)
            
            # Ensure arrays are 1D
            y_true = y_true.ravel()
            y_pred = y_pred.ravel()
            
            # Handle string labels
            if y_true.dtype.kind in ['U', 'S', 'O']:  # If labels are strings or objects
                label_encoder = LabelEncoder()
                y_true_encoded = label_encoder.fit_transform(y_true)
                # Use the same encoder for predictions to ensure matching labels
                y_pred_encoded = label_encoder.transform(y_pred)
                
                # Store label mapping for reference
                label_mapping = dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))
                logger.info(f"Label mapping: {label_mapping}")
                
                # Use encoded values for metric calculation
                y_true = y_true_encoded
                y_pred = y_pred_encoded
            
            # Handle binary and multiclass cases
            unique_classes = np.unique(y_true)
            average = 'binary' if len(unique_classes) == 2 else 'weighted'
            
            # Calculate metrics
            metrics = {
                'accuracy': float(accuracy_score(y_true, y_pred)),
                'precision': float(precision_score(y_true, y_pred, average=average, zero_division=0)),
                'recall': float(recall_score(y_true, y_pred, average=average, zero_division=0)),
                'f1': float(f1_score(y_true, y_pred, average=average, zero_division=0))
            }
            
            # Add confusion matrix
            metrics['confusion_matrix'] = confusion_matrix(y_true, y_pred).tolist()
            
            # Add detailed classification report
            metrics['classification_report'] = classification_report(y_true, y_pred)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in classification evaluation: {str(e)}")
            logger.error(f"Input shapes - y_true: {y_true.shape}, y_pred: {y_pred.shape}")
            logger.error(f"Unique values - y_true: {np.unique(y_true)}, y_pred: {np.unique(y_pred)}")
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'error': str(e)
            }

    @staticmethod
    def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Evaluate regression model performance.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary containing regression metrics
        """
        try:
            # Convert pandas Series to numpy arrays if needed
            if hasattr(y_true, 'to_numpy'):
                y_true = y_true.to_numpy()
            if hasattr(y_pred, 'to_numpy'):
                y_pred = y_pred.to_numpy()
                
            # Ensure arrays are 1D
            y_true = y_true.ravel()
            y_pred = y_pred.ravel()
            
            # Calculate metrics
            mse = float(mean_squared_error(y_true, y_pred))
            rmse = float(np.sqrt(mse))
            mae = float(mean_absolute_error(y_true, y_pred))
            r2 = float(r2_score(y_true, y_pred))
            
            # Calculate additional metrics
            explained_variance = float(1 - np.var(y_true - y_pred) / np.var(y_true))
            
            metrics = {
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'r2': r2,
                'explained_variance': explained_variance
            }
            
            # Log the shapes and sample of values for debugging
            logger.info(f"Regression evaluation shapes - y_true: {y_true.shape}, y_pred: {y_pred.shape}")
            logger.info(f"Sample values - y_true[:5]: {y_true[:5]}, y_pred[:5]: {y_pred[:5]}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in regression evaluation: {str(e)}")
            logger.error(f"Input types - y_true: {type(y_true)}, y_pred: {type(y_pred)}")
            if hasattr(y_true, 'shape'):
                logger.error(f"y_true shape: {y_true.shape}")
            if hasattr(y_pred, 'shape'):
                logger.error(f"y_pred shape: {y_pred.shape}")
            return {
                'mse': float('inf'),
                'rmse': float('inf'),
                'mae': float('inf'),
                'r2': 0.0,
                'explained_variance': 0.0,
                'error': str(e)
            }

    @staticmethod
    def evaluate_clustering(X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """
        Evaluate clustering model performance.
        
        Args:
            X: Input features
            labels: Cluster labels
            
        Returns:
            Dictionary containing clustering metrics
        """
        try:
            # Only calculate metrics if there are at least 2 clusters
            n_clusters = len(np.unique(labels[labels != -1]))  # Exclude noise points (-1)
            
            if n_clusters < 2:
                return {
                    'silhouette': 0.0,
                    'calinski_harabasz': 0.0,
                    'davies_bouldin': 0.0,
                    'n_clusters': n_clusters,
                    'error': 'Not enough clusters for evaluation'
                }
            
            metrics = {}
            
            # Silhouette Score (-1 to 1, higher is better)
            try:
                metrics['silhouette'] = float(silhouette_score(X, labels))
            except:
                metrics['silhouette'] = 0.0
            
            # Calinski-Harabasz Index (higher is better)
            try:
                metrics['calinski_harabasz'] = float(calinski_harabasz_score(X, labels))
            except:
                metrics['calinski_harabasz'] = 0.0
            
            # Davies-Bouldin Index (lower is better)
            try:
                metrics['davies_bouldin'] = float(davies_bouldin_score(X, labels))
            except:
                metrics['davies_bouldin'] = float('inf')
            
            # Additional clustering statistics
            metrics.update({
                'n_clusters': int(n_clusters),
                'cluster_sizes': [int(sum(labels == i)) for i in range(n_clusters)],
                'noise_points': int(sum(labels == -1)) if -1 in labels else 0
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in clustering evaluation: {str(e)}")
            return {
                'silhouette': 0.0,
                'calinski_harabasz': 0.0,
                'davies_bouldin': float('inf'),
                'n_clusters': 0,
                'error': str(e)
            }


    @staticmethod
    def evaluate(y_true: np.ndarray, y_pred: np.ndarray, task: str = 'classification', X: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Evaluate model performance based on the task type.
        
        Args:
            y_true: True values/labels
            y_pred: Predicted values/labels
            task: Type of task ('classification', 'regression', or 'clustering')
            X: Input features (required for clustering evaluation)
            
        Returns:
            Dictionary containing appropriate metrics
        """
        try:
            # Input validation
            if task.lower() == 'clustering':
                if X is None:
                    raise ValueError("Input features (X) are required for clustering evaluation")
                return ModelEvaluator.evaluate_clustering(X, y_pred)
            
            if y_true is None or y_pred is None:
                raise ValueError("Input arrays cannot be None")
            
            # Convert inputs to numpy arrays
            y_true = np.asarray(y_true)
            y_pred = np.asarray(y_pred)
            
            # Ensure arrays are 1D
            y_true = y_true.ravel()
            y_pred = y_pred.ravel()
            
            logger.info(f"Evaluation input shapes - y_true: {y_true.shape}, y_pred: {y_pred.shape}")
            logger.info(f"Unique values - y_true: {np.unique(y_true)}, y_pred: {np.unique(y_pred)}")
            
            if len(y_true) != len(y_pred):
                raise ValueError(f"Length mismatch between true ({len(y_true)}) and predicted ({len(y_pred)}) values")
            
            if len(y_true) == 0:
                raise ValueError("Empty input arrays")
            
            # Handle NaN values
            mask = ~(np.isnan(y_true) | np.isnan(y_pred))
            y_true = y_true[mask]
            y_pred = y_pred[mask]
            
            if len(y_true) == 0:
                raise ValueError("No valid data points after removing NaN values")
            
            # Evaluate based on task type
            if task.lower() == 'classification':
                return ModelEvaluator.evaluate_classification(y_true, y_pred)
            elif task.lower() == 'regression':
                return ModelEvaluator.evaluate_regression(y_true, y_pred)
            else:
                raise ValueError(f"Unknown task type: {task}")
                
        except Exception as e:
            logger.error(f"Error in model evaluation: {str(e)}")
            return {
                'error': str(e),
                'task': task,
                'status': 'failed'
            }