from flask import flash, redirect, url_for, render_template, session, request,send_file
from flask_login import login_required
from sklearn.preprocessing import LabelEncoder
import pandas as pd
from .data_loader import DataLoader
import io
import time

data_loader = DataLoader()

def manuelle_cleaning_logic():
    file_id = session.get('cleaning_file_id')
    if not file_id:
        flash("Please upload a file first", 'error')
        return redirect(url_for('data_cleaning'))

    try:
        df = data_loader.load_dataframe(file_id)
        if df is None:
            flash("Could not load data", 'error')
            return redirect(url_for('data_cleaning'))

        # Calcul des statistiques avant nettoyage
        original_row_count = len(df)
        duplicated_count_before = df.duplicated().sum()

        if request.method == 'POST':
            # Suppression des colonnes
            columns_to_remove = request.form.getlist('columns_to_remove')
            if columns_to_remove:
                existing_columns = [col for col in columns_to_remove if col in df.columns]
                df.drop(columns=existing_columns, inplace=True)
                data_loader.save_dataframe(df, file_id)
                session['cleaning_file_id'] = file_id
                flash(f"Columns {', '.join(existing_columns)} removed successfully", 'success')

            # Remplissage des colonnes numériques
            numeric_fill_method = request.form.getlist('numeric_fill_method')
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            numeric_null_columns = [col for col in numeric_columns if df[col].isnull().any()]

            for col, method in zip(numeric_null_columns, numeric_fill_method):
                if method == 'mean':
                    df[col].fillna(df[col].mean(), inplace=True)
                elif method == 'median':
                    df[col].fillna(df[col].median(), inplace=True)

            # Remplissage des colonnes catégorielles
            categorical_fill_method = request.form.getlist('categorical_fill_method')
            categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
            categorical_null_columns = [col for col in categorical_columns if df[col].isnull().any()]

            for col, method in zip(categorical_null_columns, categorical_fill_method):
                if method == 'mode':
                    df[col].fillna(df[col].mode()[0], inplace=True)
                elif method == 'bfill':
                    df[col].fillna(method='bfill', inplace=True)

            # Encodage des colonnes catégorielles si nécessaire
            for col in categorical_columns:
                if df[col].nunique() < 6 or df[col].dtype == 'bool':
                    try:
                        label_encoder = LabelEncoder()
                        df[col] = label_encoder.fit_transform(df[col].astype(str))
                    except Exception as e:
                        flash(f"Error encoding column {col}: {str(e)}", 'error')

            # Encodage des colonnes booléennes
            boolean_columns = df.select_dtypes(include=['bool']).columns.tolist()
            for col in boolean_columns:
                df[col] = df[col].astype(int)

            # Sauvegarde des modifications
            data_loader.save_dataframe(df, file_id)
            session['cleaning_file_id'] = file_id
            flash("Data cleaning applied successfully", 'success')

        # Nettoyage automatique des doublons
        df.drop_duplicates(inplace=True)

        # Sauvegarde des données nettoyées
        cleaned_file_id = data_loader.generate_file_id()
        data_loader.save_dataframe(df, cleaned_file_id)
        session['cleaned_file_id'] = cleaned_file_id

        # Calcul des statistiques après nettoyage
        duplicated_count_after = df.duplicated().sum()
        current_row_count_after = len(df)

        # Calcul des statistiques supplémentaires
        null_percentage = df.isnull().mean() * 100
        high_null_columns = null_percentage[null_percentage > 40].index.tolist()
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        null_columns = df.columns[df.isnull().any()].tolist()
        null_counts = df[null_columns].isnull().sum().to_dict() if null_columns else {}
        numeric_null_columns = [col for col in numeric_columns if col in null_columns]
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        categorical_null_columns = [col for col in categorical_columns if df[col].isnull().any()]

        return render_template(
            'Manuelle_Cleaning.html',
            data=df.head(5),
            numeric_columns=numeric_columns,
            null_columns=null_columns,
            null_counts=null_counts,
            numeric_null_columns=numeric_null_columns,
            all_columns=df.columns.tolist(),
            categorical_null_columns=categorical_null_columns,
            categorical_columns=categorical_columns,
            duplicated_count_before=duplicated_count_before,
            duplicated_count_after=duplicated_count_after,
            original_row_count=original_row_count,
            current_row_count_after=current_row_count_after,
            high_null_columns=high_null_columns,
            null_percentage=null_percentage.to_dict()
        )

    except Exception as e:
        flash(f"Error cleaning data: {str(e)}", 'error')
        return render_template(
            'Manuelle_Cleaning.html',
            data=None,
            numeric_columns=[],
            null_columns=[],
            numeric_null_columns=[],
            all_columns=[],
            categorical_null_columns=[],
            categorical_columns=[],
            duplicated_count_before=0,
            duplicated_count_after=0,
            original_row_count=0,
            current_row_count_after=0
        )
    

# Ajout de la fonction de nettoyage automatique
def remplir_valeurs_manquantes(df):
    if df.empty:
        raise ValueError("Le DataFrame est vide, aucun nettoyage possible.")
    
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        if df[col].isnull().sum() > 0:
            try:
                skewness = df[col].skew()
                if abs(skewness) < 0.5:
                    df[col] = df[col].fillna(df[col].mean())
                elif 0.5 <= abs(skewness) <= 1.5:
                    df[col] = df[col].fillna(df[col].median())
                else:
                    df[col] = df[col].fillna(df[col].quantile(0.75))
            except Exception as e:
                df[col] = df[col].fillna(df[col].median())
    return df

def automatic_cleaning_logic():
    file_id = session.get('cleaning_file_id')
    if not file_id:
        flash("Please upload a file first", 'error')
        return redirect(url_for('data_cleaning'))
    
    try:
        df = data_loader.load_dataframe(file_id)
        if df is None:
            flash("Could not load data", 'error')
            return redirect(url_for('data_cleaning'))
        
        # Store original stats
        original_stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'null_values': df.isnull().sum().sum(),
            'duplicates': df.duplicated().sum(),
            'categorical_cols': len(df.select_dtypes(include=['object']).columns),
            'numeric_cols': len(df.select_dtypes(include=['int64', 'float64']).columns),
            'boolean_cols': len(df.select_dtypes(include=['bool']).columns)
        }

        # Perform cleaning operations
        df = df.drop_duplicates()

        cleaning_operations = {
            'encoded_columns': [],
            'filled_numeric': [],
            'filled_categorical': [],
            'removed_duplicates': original_stats['duplicates'],
            'removed_columns': []
        }
        
        # Handle categorical and boolean columns
        categorical = df.select_dtypes(include=['object', 'bool']).columns.tolist()
        for col in categorical:
            if df[col].dtype == 'bool':
                df[col] = df[col].astype(int)
                cleaning_operations['encoded_columns'].append(col)
            elif df[col].dtype == 'object':
                if df[col].nunique() <= 6:
                    label_encoder = LabelEncoder()
                    df[col] = label_encoder.fit_transform(df[col].astype(str))
                    cleaning_operations['encoded_columns'].append(col)
        
        # Fill missing values
        for column in df.columns:
            if df[column].isnull().any():
                if df[column].dtype in ['int64', 'float64', 'bool']:
                    mean_value = df[column].mean()
                    df[column].fillna(mean_value, inplace=True)
                    cleaning_operations['filled_numeric'].append(column)
                else:
                    mode_value = df[column].mode()[0] if not df[column].mode().empty else 'Unknown'
                    df[column].fillna(mode_value, inplace=True)
                    cleaning_operations['filled_categorical'].append(column)
        
        # Remove columns with >40% null values
        null_percentage = df.isnull().mean() * 100
        columns_to_remove = null_percentage[null_percentage > 40].index.tolist()
        if columns_to_remove:
            df = df.drop(columns=columns_to_remove)
            cleaning_operations['removed_columns'].extend(columns_to_remove)

        final_stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'null_values': df.isnull().sum().sum(),
            'duplicates': df.duplicated().sum(),
            'categorical_cols': len(df.select_dtypes(include=['object']).columns),
            'numeric_cols': len(df.select_dtypes(include=['int64', 'float64']).columns),
            'boolean_cols': len(df.select_dtypes(include=['bool']).columns)
        }

        cleaned_file_id = data_loader.generate_file_id()
        data_loader.save_dataframe(df, cleaned_file_id)
        session['cleaned_file_id'] = cleaned_file_id
        
        return render_template('automatic_cleaning.html',
                               data=df,
                               original_stats=original_stats,
                               final_stats=final_stats,
                               cleaning_operations=cleaning_operations)
    
    except Exception as e:
        flash(f"Error cleaning data: {str(e)}", 'error')
        return render_template('automatic_cleaning.html', data=None)


def download_cleaned_data_logic():
    file_id = session.get('cleaned_file_id')
    if not file_id:
        flash("No cleaned data available", 'error')
        return redirect(url_for('data_cleaning'))
    
    try:
        df = data_loader.load_dataframe(file_id)
        if df is None:
            flash("Could not load cleaned data", 'error')
            return redirect(url_for('automatic_cleaning'))

        # Create CSV in memory
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='cleaned_data.csv'
        )
    except Exception as e:
        flash(f"Error downloading data: {str(e)}", 'error')
        return redirect(url_for('automatic_cleaning'))
