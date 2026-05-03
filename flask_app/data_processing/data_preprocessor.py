import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

class DataPreprocessor:
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.imputer = SimpleImputer(strategy='mean')
        self.categorical_imputer = SimpleImputer(strategy='most_frequent')
        self.target_scaler = None
        self.feature_names = None
        
    def handle_missing_values(self, df):
        """Handle missing values in the dataset"""
        # Create a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        categorical_columns = df.select_dtypes(exclude=[np.number]).columns
        
        # Handle numeric columns
        if len(numeric_columns) > 0:
            numeric_data = self.imputer.fit_transform(df[numeric_columns])
            df[numeric_columns] = pd.DataFrame(numeric_data, columns=numeric_columns, index=df.index)
            
        # Handle categorical columns
        if len(categorical_columns) > 0:
            categorical_data = self.categorical_imputer.fit_transform(df[categorical_columns])
            df[categorical_columns] = pd.DataFrame(categorical_data, columns=categorical_columns, index=df.index)
            
        return df
    
    def encode_categorical_variables(self, df):
        """Encode categorical variables using label encoding"""
        # Create a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        categorical_columns = df.select_dtypes(exclude=[np.number]).columns
        
        for col in categorical_columns:
            try:
                # Use label encoding for all categorical variables
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
            except Exception as e:
                print(f"Error encoding column {col}: {str(e)}")
        
        return df

    def preprocess_data(self, df, target_variable=None, task='classification'):
        """
        Preprocess data based on the task type
        
        Args:
            df: Input DataFrame
            target_variable: Target variable name (optional for clustering)
            task: Type of task ('classification', 'regression', or 'clustering')
        """
        try:
            # Create a copy to avoid SettingWithCopyWarning
            df = df.copy()
            
            # Handle missing values
            df = self.handle_missing_values(df)
            
            # Remove duplicates
            df = self.remove_duplicates(df)
            
            if target_variable is not None:
                # Split features and target
                X = df.drop(columns=[target_variable])
                y = df[target_variable]
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # Encode categorical variables
                X_train = self.encode_categorical_variables(X_train)
                X_test = self.encode_categorical_variables(X_test)
                
                # Scale features while preserving column names
                X_train_scaled = pd.DataFrame(
                    self.scaler.fit_transform(X_train),
                    columns=X_train.columns,
                    index=X_train.index
                )
                X_test_scaled = pd.DataFrame(
                    self.scaler.transform(X_test),
                    columns=X_test.columns,
                    index=X_test.index
                )

                # Handle target variable based on task
                if task == 'regression':
                    print(f"Target variable statistics:")
                    print(f"Train - Mean: {y_train.mean()}, Std: {y_train.std()}, Range: [{y_train.min()}, {y_train.max()}]")
                    print(f"Test - Mean: {y_test.mean()}, Std: {y_test.std()}, Range: [{y_test.min()}, {y_test.max()}]")
                    
                elif task == 'classification':
                    try:
                        # Print class distribution
                        class_counts = y_train.value_counts()
                        print("Original class distribution:", class_counts)
                        
                        # Apply SMOTE only if significant imbalance exists
                        imbalance_ratio = class_counts.max() / class_counts.min()
                        if imbalance_ratio > 1.5:
                            print(f"Detected class imbalance (ratio: {imbalance_ratio:.2f}). Applying SMOTE...")
                            smote = SMOTE(random_state=42, k_neighbors=min(5, min(class_counts)-1))
                            X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
                            
                            # Convert back to DataFrame/Series
                            X_train_scaled = pd.DataFrame(X_train_resampled, columns=X_train.columns)
                            y_train = pd.Series(y_train_resampled, index=X_train_scaled.index)
                            
                            # Print new distribution
                            print("Balanced class distribution:", y_train.value_counts())
                        else:
                            print("No significant class imbalance detected.")
                            
                    except Exception as e:
                        print(f"Warning: Could not apply SMOTE: {str(e)}")
            
                return X_train_scaled, X_test_scaled, y_train, y_test
            
            elif task == 'clustering':
                # For clustering, we only need to scale the data
                df_scaled = pd.DataFrame(
                    self.scaler.fit_transform(df),
                    columns=df.columns,
                    index=df.index
                )
                # For clustering, return the same data for train and test
                return df_scaled, df_scaled, None, None
                
        except Exception as e:
            print(f"Error in preprocessing pipeline: {str(e)}")
            raise
            
    def inverse_transform_target(self, y_pred):
        """
        Inverse transform scaled target variable predictions
        
        Args:
            y_pred: Scaled predictions
            
        Returns:
            Original scale predictions
        """
        if self.target_scaler is None:
            return y_pred
            
        try:
            # Ensure y_pred is 2D for inverse transform
            y_pred_2d = y_pred.reshape(-1, 1) if len(y_pred.shape) == 1 else y_pred
            return self.target_scaler.inverse_transform(y_pred_2d).ravel()
        except Exception as e:
            print(f"Error in inverse transform: {str(e)}")
            return y_pred

    def detect_outliers(self, df):
        """Detect outliers using IQR method"""
        Q1 = df.quantile(0.25)
        Q3 = df.quantile(0.75)
        IQR = Q3 - Q1
        outlier_mask = ~((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).any(axis=1)
        return outlier_mask
    
    def remove_duplicates(self, df):
        """Remove duplicates from the dataset"""
        return df.drop_duplicates() 
    
    def remove_outliers(self, df):
        """Remove outliers from the dataset using IQR method"""
        outlier_mask = self.detect_outliers(df)
        return df[outlier_mask]
    
    def apply_smote(self, X_train, y_train):
        """Apply SMOTE to balance the dataset"""
        try:
            class_counts = y_train.value_counts()
            imbalance_ratio = class_counts.max() / class_counts.min()
            
            if imbalance_ratio > 1.5 and class_counts.min() > 1:
                smote = SMOTE(random_state=42)
                X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
                return X_train_res, y_train_res
            else:
                return X_train, y_train
        except Exception as e:
            print(f"Error applying SMOTE: {str(e)}")
            return X_train, y_train

    def preprocess_features(self, X):
        """Preprocess feature variables"""
        try:
            # Handle missing values
            X = self.handle_missing_values(X)
            
            # Encode categorical variables
            X = self.encode_categorical_variables(X)
            
            # Scale features
            X = pd.DataFrame(
                self.scaler.fit_transform(X),
                columns=X.columns,
                index=X.index
            )
            
            return X
        except Exception as e:
            print(f"Error preprocessing features: {str(e)}")
            raise

    def preprocess_target(self, y):
        """Preprocess target variable"""
        try:
            # Handle missing values
            y = y.dropna()
            
            # For categorical target (classification)
            if y.dtype == 'object' or y.dtype.name == 'category':
                y = self.label_encoder.fit_transform(y.astype(str))
            
            return y
        except Exception as e:
            print(f"Error preprocessing target: {str(e)}")
            raise
