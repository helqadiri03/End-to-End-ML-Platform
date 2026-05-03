from visualization.basic_plots import create_visualization
from flask import render_template, redirect, url_for, session, flash, send_file,make_response
from .data_loader import DataLoader
import pandas as pd
from scipy import stats
from docx import Document
from weasyprint import HTML,CSS
import pickle
import os
import traceback
import glob


data_loader = DataLoader()

def generate_report_route():
    file_id = session.get('cleaned_file_id')
    if not file_id:
        flash("No cleaned data available. Please upload a file for cleaning first.", 'error')
        return redirect(url_for('analyse'))
    
    try:
        # Chargement des données nettoyées
        df = data_loader.load_dataframe(file_id)
        if df is None or df.empty:
            flash("Could not load cleaned data or the data is empty.", 'error')
            return redirect(url_for('analyse'))

        # Statistiques globales étendues
        original_stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'null_values': df.isnull().sum().sum(),
            'duplicates': df.duplicated().sum(),
            'categorical_cols': df.select_dtypes(include='object').shape[1],
            'numeric_cols': df.select_dtypes(include=['number']).shape[1],
            'memory_usage': df.memory_usage(deep=True).sum() / 1024**2,  # En MB
            'date_cols': len([col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]),
            'unique_values_per_column': {col: df[col].nunique() for col in df.columns}
        }

        # Statistiques avancées pour colonnes numériques
        numeric_cols = df.select_dtypes(include=['number']).columns
        advanced_numeric_stats = {}
        for col in numeric_cols:
            advanced_numeric_stats[col] = {
                'basic_stats': df[col].describe().to_dict(),
                'skewness': stats.skew(df[col].dropna()),
                'kurtosis': stats.kurtosis(df[col].dropna()),
                'outliers': len(df[df[col] > df[col].mean() + 3 * df[col].std()]) + 
                           len(df[df[col] < df[col].mean() - 3 * df[col].std()]),
                'missing_percentage': (df[col].isnull().sum() / len(df)) * 100
            }

        # Analyse des corrélations
        correlation_matrix = df[numeric_cols].corr()
        strong_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                if abs(correlation_matrix.iloc[i, j]) > 0.7:
                    strong_correlations.append({
                        'col1': numeric_cols[i],
                        'col2': numeric_cols[j],
                        'correlation': correlation_matrix.iloc[i, j]
                    })

        # Analyse des valeurs catégorielles
        categorical_stats = {}
        for col in df.select_dtypes(include='object').columns:
            value_counts = df[col].value_counts()
            categorical_stats[col] = {
                'unique_values': df[col].nunique(),
                'top_5_values': value_counts.head().to_dict(),
                'missing_percentage': (df[col].isnull().sum() / len(df)) * 100
            }

        # Visualisations étendues
        visualizations = []
        for col in numeric_cols[:4]:  # Histogrammes pour colonnes numériques
            viz_data = create_visualization(df, 'histogram', [col], f'Distribution of {col}')
            if viz_data:
                visualizations.append(_create_viz_dict(f'Distribution of {col}', viz_data))
        if len(numeric_cols) > 1:  # Scatter plots pour relations entre variables numériques
            for i in range(len(numeric_cols)):
                for j in range(i + 1, min(i + 3, len(numeric_cols))):  # Limite le nombre de combinaisons
                    col_x, col_y = numeric_cols[i], numeric_cols[j]
                    viz_data = create_visualization(df, 'scatter', [col_x, col_y], f'Scatter Plot of {col_x} vs {col_y}')
                    if viz_data:
                        visualizations.append(_create_viz_dict(f'Scatter Plot of {col_x} vs {col_y}', viz_data))
        if len(numeric_cols) > 1:  # Correlation heatmap
            viz_data = create_visualization(df, 'heatmap', numeric_cols, 'Correlation Heatmap')
            if viz_data:
                visualizations.append(_create_viz_dict('Correlation Heatmap', viz_data))

        # Résultats des modèles
        model_statuses = session.get('model_statuses', {})

        models_results = []
        for model_name, status in model_statuses.items():
            if status['status'] == 'complete':
                model_files = glob.glob(f"temp_data/models/{model_name}_*.pkl")
                if model_files:
                    model_path = model_files[0]
                    print(f"Using model file: {model_path}")
                    try:
                        with open(model_path, 'rb') as f:
                            model_data = pickle.load(f)
                            metrics = model_data.get('metrics', {})
                            if metrics:  # Vérifiez que les métriques ne sont pas vides
                                models_results.append({
                                    'name': model_name.replace('_', ' ').title(),
                                    'metrics': metrics
                                })
                                print(f"Loaded model: {model_name}, Metrics: {metrics}")
                            else:
                                print(f"No metrics found for model {model_name}")
                    except Exception as e:
                        print(f"Error loading model {model_name}: {str(e)}")
                        traceback.print_exc()
                else:
                    print(f"No model file found for {model_name}")

        if not models_results:
            flash("No completed models found. Cannot generate report.", 'error')
            return redirect(url_for('analyse'))


        # Détecter automatiquement la tâche
        task = None
        for model in models_results:
            metrics = model.get('metrics', {})
            if 'accuracy' in metrics:
                task = 'classification'
                break
            elif 'r2' in metrics:
                task = 'regression'
                break
            elif 'silhouette' in metrics:
                task = 'clustering'
                break

        if not task:
            flash("Could not detect the task type from model results.", 'error')
            return redirect(url_for('analyse'))


        # Rendu du rapport
        return render_template('report.html',
                               original_stats=original_stats,
                               advanced_numeric_stats=advanced_numeric_stats,
                               categorical_stats=categorical_stats,
                               strong_correlations=strong_correlations,
                               visualizations=visualizations,
                               models_results=models_results,
                               task=task)

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        traceback.print_exc()
        flash(f"Error generating report: {str(e)}", 'error')
        return redirect(url_for('analyse'))


def _create_viz_dict(title, viz_data):
    return {
        'title': title,
        'img': viz_data['plot_data'],
        'type': viz_data['plot_type'],
        'description': _generate_viz_description(title, viz_data)
    }

def _generate_viz_description(title, viz_data):
    """
    Génère une description automatique pour chaque visualisation
    """
    if 'Distribution' in title:
        return "Cette visualisation montre la distribution des valeurs dans la colonne. " \
               "Elle permet d'identifier la forme de la distribution, les pics et les anomalies potentielles."
    elif 'Density' in title:
        return "Ce density plot montre une version lissée de l'histogramme, mettant en évidence les zones à forte densité de données."
    elif 'Correlation' in title:
        return "Cette matrice de corrélation montre les relations entre les différentes variables numériques du dataset."
    return "Visualisation des données pour analyse exploratoire."



def download_pdf_route():
    file_id = session.get('cleaned_file_id')
    if not file_id:
        flash("No cleaned data available. Please upload a file for cleaning first.", 'error')
        return redirect(url_for('analyse'))
    
    try:
        df = data_loader.load_dataframe(file_id)
        if df is None:
            flash("Could not load cleaned data", 'error')
            return redirect(url_for('analyse'))
        
        # --- Reprend la logique de preparation des données (mêmes calculs que dans generate_report_route) ---
        original_stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'null_values': df.isnull().sum().sum(),
            'duplicates': df.duplicated().sum(),
            'categorical_cols': df.select_dtypes(include='object').shape[1],
            'numeric_cols': df.select_dtypes(include=['number']).shape[1],
            'memory_usage': df.memory_usage(deep=True).sum() / 1024**2,
            'date_cols': len([col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]),
            'unique_values_per_column': {col: df[col].nunique() for col in df.columns}
        }
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        advanced_numeric_stats = {}
        for col in numeric_cols:
            advanced_numeric_stats[col] = {
                'basic_stats': df[col].describe().to_dict(),
                'skewness': stats.skew(df[col].dropna()),
                'kurtosis': stats.kurtosis(df[col].dropna()),
                'outliers': len(df[df[col] > df[col].mean() + 3*df[col].std()]) + 
                            len(df[df[col] < df[col].mean() - 3*df[col].std()]),
                'missing_percentage': (df[col].isnull().sum() / len(df)) * 100
            }
        
        correlation_matrix = df[numeric_cols].corr()
        strong_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                if abs(correlation_matrix.iloc[i,j]) > 0.7:
                    strong_correlations.append({
                        'col1': numeric_cols[i],
                        'col2': numeric_cols[j],
                        'correlation': correlation_matrix.iloc[i,j]
                    })
        
        categorical_stats = {}
        for col in df.select_dtypes(include='object').columns:
            value_counts = df[col].value_counts()
            categorical_stats[col] = {
                'unique_values': df[col].nunique(),
                'top_5_values': value_counts.head().to_dict(),
                'missing_percentage': (df[col].isnull().sum() / len(df)) * 100
            }
        
        # Visualisations (mêmes opérations que dans generate_report_route)
        visualizations = []
        for col in numeric_cols[:4]:
            viz_data = create_visualization(df, 'histogram', [col], f'Distribution of {col}')
            if viz_data:
                visualizations.append(_create_viz_dict(f'Distribution of {col}', viz_data))

        if len(numeric_cols) > 1:  # Scatter plots pour relations entre variables numériques
            for i in range(len(numeric_cols)):
                for j in range(i + 1, min(i + 3, len(numeric_cols))):  # Limite le nombre de combinaisons
                    col_x, col_y = numeric_cols[i], numeric_cols[j]
                    viz_data = create_visualization(df, 'scatter', [col_x, col_y], f'Scatter Plot of {col_x} vs {col_y}')
                    if viz_data:
                        visualizations.append(_create_viz_dict(f'Scatter Plot of {col_x} vs {col_y}', viz_data))

        if len(numeric_cols) > 1:
            viz_data = create_visualization(df, 'heatmap', numeric_cols, 'Correlation Heatmap')
            if viz_data:
                visualizations.append(_create_viz_dict('Correlation Heatmap', viz_data))


                # Résultats des modèles
        model_statuses = session.get('model_statuses', {})

        models_results = []
        for model_name, status in model_statuses.items():
            if status['status'] == 'complete':
                model_files = glob.glob(f"temp_data/models/{model_name}_*.pkl")
                if model_files:
                    model_path = model_files[0]
                    print(f"Using model file: {model_path}")
                    try:
                        with open(model_path, 'rb') as f:
                            model_data = pickle.load(f)
                            metrics = model_data.get('metrics', {})
                            models_results.append({
                                'name': model_name.replace('_', ' ').title(),
                                'metrics': metrics
                            })
                            print(f"Loaded model: {model_name}, Metrics: {metrics}")
                    except Exception as e:
                        print(f"Error loading model {model_name}: {str(e)}")
                        traceback.print_exc()
                else:
                    print(f"No model file found for {model_name}")

        if not models_results:
            flash("No completed models found. Cannot generate report.", 'error')
            return redirect(url_for('analyse'))


        # Détecter automatiquement la tâche
        task = None
        for model in models_results:
            metrics = model.get('metrics', {})
            if 'accuracy' in metrics:
                task = 'classification'
                break
            elif 'r2' in metrics:
                task = 'regression'
                break
            elif 'silhouette' in metrics:
                task = 'clustering'
                break
        
        # Rendu du template en HTML
        html_content = render_template('report.html',
            original_stats=original_stats,
            advanced_numeric_stats=advanced_numeric_stats,
            categorical_stats=categorical_stats,
            strong_correlations=strong_correlations,
            visualizations=visualizations,
            models_results=models_results,
            task=task,
            pdf_mode=True,
            pdf_class='pdf-report'  
        )

        # Génération du PDF avec WeasyPrint
        css_string = """
            @page { 
                size: A4; 
                margin: 2cm; 
            }
            .pdf-report header,
            .pdf-report .header,
            .pdf-report footer,
            .pdf-report .footer,
            .pdf-report nav {
                display: none !important;
            }
            .pdf-report main {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }
            @media print { 
                body { 
                    -webkit-print-color-adjust: exact; 
                }
            }
        """
        # Génération du PDF avec WeasyPrint
        html = HTML(string=html_content)
        pdf = html.write_pdf(stylesheets=[CSS(string=css_string)])

        # Renvoi du PDF en pièce jointe téléchargeable
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=report.pdf'
        return response
    
    except Exception as e:
        flash(f"Error generating report PDF: {str(e)}", 'error')
        return redirect(url_for('analyse'))