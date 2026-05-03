from sklearn.decomposition import PCA as SklearnPCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
import numpy as np
import pandas as pd
import pickle
from models.base_model import BaseModel

class PCAModel(BaseModel):
    def __init__(self, n_components=None):
        self.n_components = n_components
        self.pca = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.target_column = None
        self.explained_variance_ratio_ = None
        self.cumulative_variance_ratio_ = None
        
    def train(self, data, target_column=None):
        try:
            print(f"Starting PCA training with {self.n_components} components")
            
            # Store target column name
            self.target_column = target_column
            
            # Separate features and target
            if target_column and target_column in data.columns:
                X = data.drop(columns=[target_column])
                y = data[target_column]
            else:
                X = data
                y = None
            
            # Store feature names
            self.feature_names = X.columns.tolist()
            
            # Convert to numpy array if not already
            X = X.to_numpy() if isinstance(X, pd.DataFrame) else X
            
            # Scale the data
            X_scaled = self.scaler.fit_transform(X)
            
            # Initialize and fit PCA
            self.pca = SklearnPCA(n_components=self.n_components)
            self.pca.fit(X_scaled)
            
            # Store explained variance ratios
            self.explained_variance_ratio_ = self.pca.explained_variance_ratio_
            self.cumulative_variance_ratio_ = np.cumsum(self.explained_variance_ratio_)
            
            print("PCA training completed successfully")
            return True
            
        except Exception as e:
            print(f"Error in PCA training: {str(e)}")
            return False
    
    def transform(self, data):
        try:
            print("Starting PCA transformation")
            print(f"Input data shape: {data.shape}")
            
            # Separate features and target if needed
            if self.target_column and self.target_column in data.columns:
                X = data.drop(columns=[self.target_column])
                y = data[self.target_column]
            else:
                X = data
                y = None
            
            # Ensure we're using the same features as during training
            if isinstance(X, pd.DataFrame):
                X = X[self.feature_names]
            
            # Convert to numpy array if not already
            X = X.to_numpy() if isinstance(X, pd.DataFrame) else X
            
            # Scale the data
            X_scaled = self.scaler.transform(X)
            
            # Transform the data
            X_transformed = self.pca.transform(X_scaled)
            
            # Create column names for transformed data
            transformed_columns = [f'PC{i+1}' for i in range(X_transformed.shape[1])]
            
            # Convert to DataFrame
            transformed_df = pd.DataFrame(X_transformed, columns=transformed_columns)
            
            # Add target column back if it existed
            if y is not None:
                transformed_df[self.target_column] = y.values
            
            print(f"Transformation completed. Output shape: {transformed_df.shape}")
            return transformed_df
            
        except Exception as e:
            print(f"Error in PCA transformation: {str(e)}")
            return None
    
    def get_metrics(self):
        if self.pca is None:
            return None
            
        return {
            'n_components': self.n_components,
            'explained_variance_ratio': self.explained_variance_ratio_.tolist(),
            'cumulative_variance_ratio': self.cumulative_variance_ratio_.tolist(),
            'feature_names': self.feature_names
        }
    
    def save_model(self, filepath):
        try:
            model_data = {
                'n_components': self.n_components,
                'pca': self.pca,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'target_column': self.target_column,
                'explained_variance_ratio_': self.explained_variance_ratio_,
                'cumulative_variance_ratio_': self.cumulative_variance_ratio_
            }
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            return True
        except Exception as e:
            print(f"Error saving PCA model: {str(e)}")
            return False
    
    def load_model(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                
            self.n_components = model_data['n_components']
            self.pca = model_data['pca']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.target_column = model_data['target_column']
            self.explained_variance_ratio_ = model_data['explained_variance_ratio_']
            self.cumulative_variance_ratio_ = model_data['cumulative_variance_ratio_']
            return True
        except Exception as e:
            print(f"Error loading PCA model: {str(e)}")
            return False
    
    def predict(self, X):
        """
        Implement predict method to satisfy BaseModel abstract class.
        For PCA, predict is the same as transform since it's a dimensionality reduction technique.
        """
        return self.transform(X)
    
    def evaluate(self, X_test, y_test=None):
        """
        Implement evaluate method to satisfy BaseModel abstract class.
        For PCA, we return the explained variance metrics.
        """
        if self.pca is None:
            return None
            
        return {
            'n_components': self.n_components,
            'explained_variance_ratio': self.explained_variance_ratio_.tolist(),
            'cumulative_variance_ratio': self.cumulative_variance_ratio_.tolist(),
            'total_variance_explained': float(self.cumulative_variance_ratio_[-1])
        }