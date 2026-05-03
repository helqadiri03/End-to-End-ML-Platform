import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash, send_file,make_response
import pandas as pd
import base64
import io
import os
import uuid
from pathlib import Path
import numpy as np
import atexit

# Import visualization functions using absolute imports
from visualization.basic_plots import create_visualization, generate_histogram
from visualization.custom_plots import create_custom_visualization
from visualization.cluster_plots import create_cluster_visualization

import psycopg2
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user,login_required
from auth.routes import auth
from auth import init_login_manager

from models.classification_models.KNN import KNNClassifier
from models.classification_models.LogisticRegression import LogisticRegressionClassifier
from models.classification_models.RandomForest import RandomForestClassifier
from models.classification_models.SVM import SVMClassifier
from models.classification_models.XGBoost import XGBoostClassifier
from models.classification_models.NaiveBayes import NaiveBayesClassifier
from data_processing.data_preprocessor import DataPreprocessor
from models.model_evaluation import ModelEvaluator

from models.regression_models.LinearRegression import LinearRegressionModel
from models.regression_models.PolynomialRegression import PolynomialRegressionModel
from models.regression_models.SVR import SVRModel
from models.regression_models.RandomForestRegression import RandomForestRegressionModel
from models.regression_models.XGBoostRegression import XGBoostRegressionModel

from models.clustering_models.KMeans import KMeansCluster
from models.clustering_models.DBSCAN import DBSCANCluster
from models.clustering_models.AgglomerativeClustering import AgglomerativeCluster
from models.dimensionality_reduction.PCA import PCAModel


from data_processing.cleaning import manuelle_cleaning_logic,automatic_cleaning_logic,download_cleaned_data_logic
from data_processing.report import generate_report_route ,download_pdf_route
from data_processing.messages import index_route , messages_route
from data_processing.data_loader import DataLoader


from flask_caching import Cache
from werkzeug.utils import secure_filename
import pickle
import time
from sklearn.preprocessing import LabelEncoder
import matplotlib.font_manager as fm
from matplotlib import rcParams
from scipy.interpolate import griddata
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json
import traceback

from dotenv import load_dotenv
from groq import Groq
import contextlib



app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'hamza_session'

# Create temp_data directory if it doesn't exist
temp_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_data')
if not os.path.exists(temp_data_dir):
    os.makedirs(temp_data_dir)
    print(f"Created temp_data directory at: {temp_data_dir}")

# Initialize cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
data_loader = DataLoader(temp_dir="temp_data")

# Add configuration for max file size (e.g., 100MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Create a temporary directory for storing uploaded data and metadata
TEMP_DIR = Path("temp_data")
TEMP_DIR.mkdir(exist_ok=True)
METADATA_DIR = TEMP_DIR / "metadata"
METADATA_DIR.mkdir(exist_ok=True)
MODELS_DIR = TEMP_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Initialize Flask-Caching
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',  # You can choose a different cache type if needed
    'CACHE_DEFAULT_TIMEOUT': 300  # Cache timeout in seconds
})

def allowed_file(filename):
    return data_loader.allowed_file(filename)

def parse_file(file):
    try:
        df = data_loader.parse_file(file)
        return df, "Success"
    except ValueError as e:
        return None, str(e)


def save_dataframe(df, file_id):
    return data_loader.save_dataframe(df, file_id)

def load_dataframe(file_id):
    return data_loader.load_dataframe(file_id)


def save_metadata(metadata, file_id):
    data_loader.save_metadata(metadata, file_id)


def load_metadata(file_id):
    return data_loader.load_metadata(file_id)


def generate_file_id():
    return data_loader.generate_file_id()


@app.route('/data-cleaning', methods=['GET', 'POST'])
@login_required
def data_cleaning():
    if request.method == 'POST':
        if 'file' not in request.files:

            flash('No file found', 'error')
            return render_template('data_cleaning.html', data=None)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return render_template('data_cleaning.html', data=None)
        
        if not allowed_file(file.filename):
            flash('Invalid file format', 'error')
            return render_template('data_cleaning.html', data=None)

        try:
            # Parse and save the file
            df, message = parse_file(file)
            
            if df is None:
                flash(message, 'error')
                return render_template('data_cleaning.html', data=None)
            
            # Generate unique file ID and save data
            file_id = generate_file_id()
            save_dataframe(df, file_id)
            
            # Save metadata
            metadata = {
                'filename': file.filename,
                'file_id': file_id,
                'timestamp': time.time()
            }
            save_metadata(metadata, file_id)
            
            # Store file_id in session (only storing the ID, not the data)
            session['cleaning_file_id'] = file_id
            
            return render_template('data_cleaning.html', data=df)

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return render_template('data_cleaning.html', data=None)

    return render_template('data_cleaning.html', data=None)


@app.route('/automatic_cleaning', methods=['GET', 'POST'])
@login_required
def automatic_cleaning():
    return automatic_cleaning_logic()

@app.route('/download_cleaned_data', methods=['GET'])
@login_required
def download_cleaned_data():
    return download_cleaned_data_logic()


@app.route('/Manuelle_Cleaning', methods=['GET', 'POST'])
@login_required
def Manuelle_Cleaning():
    return manuelle_cleaning_logic()

@app.route('/generate_report', methods=['GET'])
@login_required
def generate_report():
        return generate_report_route()

@app.route('/download_pdf_route', methods=['GET'])
@login_required
def download_pdf():
        return download_pdf_route()

@app.route('/download', methods=['GET'])
@login_required
def download():
    file_id = session.get('file_id')
    if not file_id:
        flash("No data available", 'error')
        return redirect(url_for('index'))
    
    try:
        df = load_dataframe(file_id)
        if df is None:
            flash("Could not load data", 'error')
            return redirect(url_for('index'))

        # Create CSV in memory
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='data.csv'
        )
    except Exception as e:

        flash(f"Error downloading data: {str(e)}", 'error')
        return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    return index_route()

@app.route('/messages')
@login_required
def messages():
    return messages_route()


# Flask Extensions
bcrypt = Bcrypt(app)
app.register_blueprint(auth, url_prefix='/auth')
init_login_manager(app)

@app.route('/analyse')
@login_required
def analyse():
    show_messages_button = current_user.username.lower() in ['hamza', 'yousef']
    return render_template('analyse.html', show_messages_button=show_messages_button)

@app.route('/learn_more')
@login_required
def learn_more():
    return render_template('learn_more.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        print("Upload request received")
        
        if 'file' not in request.files:
            print("No file in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        print(f"Received file: {file.filename}")
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            print(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file format. Please upload a CSV or Excel file'}), 400

        try:
            print("Processing file...")
            df, message = parse_file(file)
            
            if df is None:
                print(f"Parse failed: {message}")
                return jsonify({'error': message}), 400

            file_id = generate_file_id()
            print(f"Generated file_id: {file_id}")

            save_dataframe(df, file_id)
            save_metadata({
                'filename': file.filename,
                'file_id': file_id,
                'timestamp': time.time()
            }, file_id)

            # Add columns to response
            response_data = {
                'success': True,
                'file_id': file_id,
                'filename': file.filename,
                'columns': df.columns.tolist()
            }
            print("Upload successful")
            return jsonify(response_data), 200

        except Exception as e:
            print(f"Processing error: {str(e)}")
            return jsonify({'error': str(e)}), 400

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 400

# Add error handler for large files
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File is too large. Maximum size is 100MB'}), 413


@app.route('/visualization')
@login_required
def visualization():
    file_id = request.args.get('file_id')
    data = None
    if file_id:
        data = load_dataframe(file_id)
        # Store file_id in session for other routes to use
        session['file_id'] = file_id
    return render_template('visualization.html', data=data, file_id=file_id)

@app.route('/data_name')
@login_required
def data_name():
    file_id = session.get('file_id')
    if not file_id:
        flash('No data available. Please upload a file first.')
        return redirect(url_for('index'))
    
    try:
        df = load_dataframe(file_id)
        if df is None:
            flash('Invalid or empty dataset. Please upload a file again.')
            return redirect(url_for('visualization'))
        
        visualizations = []
        numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = [col for col in df.select_dtypes(include=['object']).columns 
                          if df[col].nunique() < 20]
        
        # 1. Correlation Heatmap for numerical columns
        if len(numerical_cols) > 1:
            viz_data = create_visualization(df, 'heatmap', numerical_cols[:6], 'Correlation Heatmap')
            if viz_data:
                visualizations.append({
                    'title': 'Correlation Heatmap',
                    'img': viz_data['plot_data'],
                    'type': 'heatmap'
                })
        
        # 2. Distribution plots for numerical columns
        for col in numerical_cols[:3]:
            viz_data = create_visualization(df, 'histogram', [col], f'Distribution of {col}')
            if viz_data:
                visualizations.append({
                    'title': f'Distribution of {col}',
                    'img': viz_data['plot_data'],
                    'type': 'histogram'
                })
        
        # 3. Box plots for numerical columns by categorical
        if categorical_cols and numerical_cols:
            for num_col in numerical_cols[:2]:
                for cat_col in categorical_cols[:2]:
                    viz_data = create_visualization(df, 'box', [cat_col, num_col], 
                                                 f'Box Plot: {num_col} by {cat_col}')
                    if viz_data:
                        visualizations.append({
                            'title': f'Box Plot: {num_col} by {cat_col}',
                            'img': viz_data['plot_data'],
                            'type': 'box'
                        })
        
        # 4. Bar plots for categorical columns
        for col in categorical_cols[:2]:
            viz_data = create_visualization(df, 'bar', [col], f'Count of {col}')
            if viz_data:
                visualizations.append({
                    'title': f'Count of {col}',
                    'img': viz_data['plot_data'],
                    'type': 'bar'
                })
        
        return render_template('data_name.html', 
                             visualizations=visualizations,
                             columns=df.columns.tolist(),
                             numerical_columns=numerical_cols,
                             categorical_columns=categorical_cols)
                             
    except Exception as e:
        print(f"Error in data_name route: {str(e)}")
        flash(f'Error analyzing data: {str(e)}')
        return redirect(url_for('visualization'))
@app.route('/create_visualization', methods=['POST'])
@login_required
def create_custom_visualization():
    try:
        # Check session
        if 'file_id' not in session:
            return jsonify({'success': False, 'error': "No data available. Please upload a file first."}), 400
            
        # Load dataframe
        df = load_dataframe(session['file_id'])
        if df is None:
            return jsonify({'success': False, 'error': "Could not load data"}), 400
            
        # Get request data
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': "No data received"}), 400
                
            plot_type = data.get('plot_type')
            columns = data.get('columns', [])
            dimension = data.get('dimension', '2d')
            
            print(f"Processing visualization - Type: {plot_type}, Dimension: {dimension}, Columns: {columns}")
        except Exception as e:
            print(f"Error parsing request data: {str(e)}")
            return jsonify({'success': False, 'error': "Invalid request data"}), 400

        # Validate inputs
        if not plot_type or not columns:
            return jsonify({'success': False, 'error': "Missing plot type or columns"}), 400

        # Validate columns exist
        for col in columns:
            if col not in df.columns:
                return jsonify({'success': False, 'error': f"Column '{col}' not found in dataset"}), 400

        # Handle 2D visualizations
        if dimension == '2d':
            # Allow single column for histogram and bar plots
            if len(columns) != 2 and plot_type not in ['histogram', 'bar']:
                return jsonify({'success': False, 'error': "2D plots require exactly 2 columns"}), 400
                
            title = f'{plot_type.capitalize()} Plot: {" vs ".join(columns)}'
            try:
                viz_data = create_visualization(df, plot_type, columns, title, dimension)
                if viz_data is None:
                    return jsonify({'success': False, 'error': "Failed to create visualization"}), 500
                    
                return jsonify({
                    'success': True,
                    'visualization': {
                        'type': '2d',
                        'title': title,
                        'data': viz_data['plot_data']
                    }
                })
            except Exception as e:
                print(f"Error creating 2D visualization: {str(e)}")
                return jsonify({'success': False, 'error': f"Error creating 2D plot: {str(e)}"}), 500

        # Handle 3D visualizations
        elif dimension == '3d':
            if len(columns) != 3:
                return jsonify({'success': False, 'error': "3D plots require exactly 3 columns"}), 400

            try:
                # Convert to numeric
                numeric_data = {}
                for col in columns:
                    numeric_data[col] = pd.to_numeric(df[col], errors='coerce')

                # Get valid indices
                valid_mask = pd.notnull(numeric_data[columns[0]]) & \
                           pd.notnull(numeric_data[columns[1]]) & \
                           pd.notnull(numeric_data[columns[2]])
                
                valid_indices = valid_mask[valid_mask].index

                if len(valid_indices) < 4:
                    return jsonify({'success': False, 'error': "Not enough valid numeric data points"}), 400

                # Check for unique values in columns
                for col in columns:
                    unique_values = len(numeric_data[col][valid_indices].unique())
                    if unique_values < 2:
                        return jsonify({'success': False, 
                                      'error': f"Column '{col}' needs at least 2 different values. Current unique values: {unique_values}"}), 400

                # Create plot data
                if plot_type == 'scatter':
                    plot_data = [{
                        'type': 'scatter3d',
                        'x': numeric_data[columns[0]][valid_indices].tolist(),
                        'y': numeric_data[columns[1]][valid_indices].tolist(),
                        'z': numeric_data[columns[2]][valid_indices].tolist(),
                        'mode': 'markers',
                        'marker': {
                            'size': 5,
                            'color': '#0F1035',
                            'opacity': 0.8
                        }
                    }]
                elif plot_type == 'line':
                    plot_data = [{
                        'type': 'scatter3d',
                        'x': numeric_data[columns[0]][valid_indices].tolist(),
                        'y': numeric_data[columns[1]][valid_indices].tolist(),
                        'z': numeric_data[columns[2]][valid_indices].tolist(),
                        'mode': 'lines+markers',
                        'line': {
                            'color': '#0F1035',
                            'width': 2
                        },
                        'marker': {
                            'size': 3,
                            'color': '#0F1035',
                            'opacity': 0.8
                        }
                    }]
                elif plot_type == 'surface':
                    try:
                        # Create DataFrame with valid data and remove any duplicates
                        valid_data = pd.DataFrame({
                            'x': numeric_data[columns[0]][valid_indices],
                            'y': numeric_data[columns[1]][valid_indices],
                            'z': numeric_data[columns[2]][valid_indices]
                        }).drop_duplicates()

                        # Basic validations with clear messages
                        if len(valid_data) < 50:
                            return jsonify({'success': False, 
                                          'error': f"Not enough valid data points for surface plot. Found {len(valid_data)} points, need at least 50. Try using scatter plot instead."}), 400

                        x_min, x_max = valid_data['x'].min(), valid_data['x'].max()
                        y_min, y_max = valid_data['y'].min(), valid_data['y'].max()
                        
                        grid_size = 30  # Reduced grid size for better stability
                        x_grid = np.linspace(x_min, x_max, grid_size)
                        y_grid = np.linspace(y_min, y_max, grid_size)
                        x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)

                        # Try different interpolation methods
                        try:
                            # First try cubic interpolation
                            z_mesh = griddata(
                                (valid_data['x'], valid_data['y']), valid_data['z'],
                                (x_mesh, y_mesh),
                                method='cubic'
                            )

                            # If cubic fails (too many NaNs), try linear
                            if np.isnan(z_mesh).sum() > (grid_size * grid_size * 0.5):
                                z_mesh = griddata(
                                    (valid_data['x'], valid_data['y']), valid_data['z'],
                                    (x_mesh, y_mesh),
                                    method='linear'
                                )

                            # Fill remaining NaN values with nearest neighbor interpolation
                            if np.isnan(z_mesh).any():
                                z_nearest = griddata(
                                    (valid_data['x'], valid_data['y']), valid_data['z'],
                                    (x_mesh, y_mesh),
                                    method='nearest'
                                )
                                z_mesh = np.where(np.isnan(z_mesh), z_nearest, z_mesh)

                            plot_data = [{
                                'type': 'surface',
                                'x': x_grid.tolist(),
                                'y': y_grid.tolist(),
                                'z': z_mesh.tolist(),
                                'colorscale': 'Viridis',
                                'showscale': True,
                                'contours': {
                                    'z': {
                                        'show': True,
                                        'usecolormap': True,
                                        'project': {'z': True}
                                    }
                                },
                                'hoverongaps': False,
                                'hoverlabel': {'bgcolor': 'white'},
                                'lighting': {
                                    'ambient': 0.8,
                                    'diffuse': 0.9,
                                    'fresnel': 0.2,
                                    'roughness': 0.5,
                                    'specular': 0.5
                                }
                            }]

                            return jsonify({
                                'success': True,
                                'visualization': {
                                    'type': '3d',
                                    'title': f'Surface Plot: {" vs ".join(columns)}',
                                    'data': json.dumps(plot_data)
                                }
                            })

                        except Exception as e:
                            print(f"Interpolation error: {str(e)}")
                            return jsonify({
                                'success': False,
                                'error': f"Could not create surface plot with these columns. Error: {str(e)}. Try selecting different columns or use scatter plot."
                            }), 400

                    except Exception as e:
                        print(f"Surface plot error: {str(e)}")
                        return jsonify({
                            'success': False,
                            'error': f"Error creating surface plot: {str(e)}. Check if your columns contain appropriate numeric data."
                        }), 400
                else:
                    return jsonify({'success': False, 'error': f"Unsupported 3D plot type: {plot_type}"}), 400

                return jsonify({
                    'success': True,
                    'visualization': {
                        'type': '3d',
                        'title': f'3D {plot_type.capitalize()} Plot: {" vs ".join(columns)}',
                        'data': json.dumps(plot_data)
                    }
                })

            except Exception as e:
                print(f"Error creating 3D visualization: {str(e)}")
                return jsonify({'success': False, 'error': f"Error creating 3D plot: {str(e)}"}), 500

        else:
            return jsonify({'success': False, 'error': f"Unsupported dimension: {dimension}"}), 400

    except Exception as e:
        print(f"Error in create_visualization: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/models')
@login_required
def models():
    return render_template('models.html')

@app.route('/process_model_selection', methods=['POST'])
@login_required
def process_model_selection():
    try:
        task = request.form.get('task')
        file_id = request.form.get('file_id')
        target_variable = request.form.get('target_variable')
        has_target = request.form.get('has_target')

        print(f"Processing model selection with: task={task}, file_id={file_id}, target={target_variable}")

        if not task or not file_id:
            flash('Missing required parameters', 'error')
            return redirect(url_for('models'))

        # Validate the file exists
        df = load_dataframe(file_id)
        if df is None:
            flash('Could not load data file', 'error')
            return redirect(url_for('models'))

        # Store parameters in session
        session['current_task'] = task
        session['current_file_id'] = file_id
        if has_target == 'true' and target_variable:
            session['target_variable'] = target_variable
        
        session.modified = True

        return redirect(url_for('model_evaluation', task=task, file_id=file_id))
        
    except Exception as e:
        print(f"Error in process_model_selection: {str(e)}")
        flash(f'Error processing model selection: {str(e)}', 'error')
        return redirect(url_for('models'))

@app.route('/result_page')
@login_required
def result_page():
    accuracy = request.args.get('accuracy', type=float)
    return render_template('result.html', accuracy=accuracy)

@app.template_filter('nl2br')
def nl2br(value):
    if value is None:
        return ""
    return value.replace('\n', '<br>')

@app.route('/clear_session', methods=['POST'])
@login_required
def clear_session():
    if 'file_id' in session:
        try:
            # Remove temporary file
            filepath = TEMP_DIR / f"{session['file_id']}.pkl"
            if filepath.exists():
                filepath.unlink()
        except Exception as e:
            print(f"Error removing temporary file: {e}")
    session.clear()
    return jsonify({'status': 'success'})

# Add cleanup function for old files
def cleanup_old_files():
    """Remove files older than 24 hours"""
    try:
        current_time = time.time()
        for file in TEMP_DIR.glob("*.pkl"):
            if current_time - file.stat().st_mtime > 86400:  # 24 hours
                file.unlink()
        for file in METADATA_DIR.glob("*.pkl"):
            if current_time - file.stat().st_mtime > 86400:  # 24 hours
                file.unlink()
    except Exception as e:

        print(f"Error cleaning up old files: {e}")

# Register cleanup functions
atexit.register(cleanup_old_files)

# Add this configuration before creating any plots
def configure_matplotlib():
    # Use a font that supports most characters
    rcParams['font.family'] = 'DejaVu Sans'
    # Fallback to a basic font if characters aren't available
    rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'Helvetica']
    # Handle missing characters gracefully
    rcParams['axes.unicode_minus'] = False
    # Increase the figure dpi for better quality
    rcParams['figure.dpi'] = 100


@app.route('/model_evaluation/<task>/<file_id>')
@login_required
def model_evaluation(task, file_id):
    try:
        if task == 'regression':
            model_statuses = {
                'linear': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'polynomial': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'svr': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'random_forest': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'xgboost': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'}
            }
        elif task == 'classification':
            model_statuses = {
                'knn': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'logistic': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'random_forest': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'svm': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'xgboost': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'naive_bayes': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'}
            }
        elif task == 'clustering':
            model_statuses = {
                'kmeans': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'dbscan': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'},
                'agglomerative': {'status': 'waiting', 'step': 1, 'message': 'Waiting...'}
            }
        else:
            flash('Invalid task type', 'error')
            return redirect(url_for('index'))

        session['current_task'] = task
        session['current_file_id'] = file_id
        session['model_statuses'] = model_statuses
        session.modified = True

        return render_template('model_evaluation.html', task=task, file_id=file_id)

    except Exception as e:
        print(f"Error in model evaluation route: {str(e)}")
        return render_template('model_evaluation.html', task=task, file_id=file_id)

@app.route('/download_model/<model_id>')
@login_required
def download_model(model_id):
    try:
        model_path = f"temp_data/models/{model_id}.pkl"
        if not os.path.exists(model_path):
            flash('Model file not found', 'error')
            task = session.get('current_task')
            file_id = session.get('current_file_id')
            if task and file_id:
                return redirect(url_for('model_evaluation', task=task, file_id=file_id))
            else:
                return redirect(url_for('models'))
            
        # Get model name from ID
        model_name = model_id.split('_')[0].replace('_', ' ').title()
        
        return send_file(
            model_path,
            as_attachment=True,
            download_name=f"{model_name.lower().replace(' ', '_')}.pkl",
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        flash(f'Error downloading model: {str(e)}', 'error')
        task = session.get('current_task')
        file_id = session.get('current_file_id')
        if task and file_id:
            return redirect(url_for('model_evaluation', task=task, file_id=file_id))
        else:
            return redirect(url_for('models'))

@app.route('/training_status/<task>/<file_id>')
@login_required
def training_status(task, file_id):
    try:
        print(f"Checking training status for task: {task}, file_id: {file_id}")
        
        model_statuses = session.get('model_statuses', {})
        if not model_statuses:
            print("No model statuses found in session")
            return jsonify({
                'status': 'error',
                'message': 'No model statuses found',
                'model_statuses': {}
            })

        # Process one waiting model at a time
        for model_name, status in model_statuses.items():
            if status['status'] == 'waiting':
                try:
                    # Load data
                    df = load_dataframe(file_id)
                    if df is None:
                        raise ValueError("Could not load data")

                    # Update status to processing
                    model_statuses[model_name]['status'] = 'loading'
                    model_statuses[model_name]['step'] = 2
                    model_statuses[model_name]['message'] = 'Training model...'
                    session['model_statuses'] = model_statuses
                    session.modified = True

                    # Initialize preprocessor
                    preprocessor = DataPreprocessor()
                    
                    try:
                        if task == 'clustering':
                            # For clustering, we don't need target variable
                            X_train, _, _, _ = preprocessor.preprocess_data(df, task='clustering')
                            
                            # Create and train clustering model
                            model = create_clustering_model(model_name)
                            if model is None:
                                raise ValueError(f"Could not create model: {model_name}")

                            # Train and evaluate
                            model.train(X_train)
                            metrics = model.evaluate(X_train)
                            
                        else:
                            # For classification/regression, we need target variable
                            target_variable = session.get('target_variable')
                            if not target_variable:
                                raise ValueError("No target variable specified")
                                
                            X_train, X_test, y_train, y_test = preprocessor.preprocess_data(
                                df, target_variable, task=task
                            )
                            
                            # Create appropriate model
                            if task == 'classification':
                                model = create_classification_model(model_name)
                            else:  # regression
                                model = create_regression_model(model_name)
                                
                            if model is None:
                                raise ValueError(f"Could not create model: {model_name}")

                            # Train and evaluate
                            model.train(X_train, y_train)
                            y_pred = model.predict(X_test)
                            metrics = model.evaluate(y_test, y_pred)

                        # Save model
                        model_id = f"{model_name}_{file_id}"
                        model.save_model(f"temp_data/models/{model_id}.pkl")
                        
                        # Update status to complete
                        model_statuses[model_name]['status'] = 'complete'
                        model_statuses[model_name]['step'] = 3
                        model_statuses[model_name]['message'] = 'Complete'
                        
                    except Exception as e:
                        print(f"Error training model {model_name}: {str(e)}")
                        model_statuses[model_name]['status'] = 'error'
                        model_statuses[model_name]['message'] = str(e)
                    
                except Exception as e:
                    print(f"Error processing data for model {model_name}: {str(e)}")
                    model_statuses[model_name]['status'] = 'error'
                    model_statuses[model_name]['message'] = str(e)
                
                session['model_statuses'] = model_statuses
                session.modified = True
                break  # Process only one model per request

        return jsonify({
            'status': 'processing',
            'message': 'Processing models...',
            'model_statuses': model_statuses
        })

    except Exception as e:
        print(f"Error in training status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'model_statuses': model_statuses if 'model_statuses' in locals() else {}
        })

def create_classification_model(model_name):
    """Helper function to create classification models"""
    model_map = {
        'knn': KNNClassifier,
        'logistic': LogisticRegressionClassifier,
        'random_forest': RandomForestClassifier,
        'svm': SVMClassifier,
        'xgboost': XGBoostClassifier,
        'naive_bayes': NaiveBayesClassifier
    }
    return model_map.get(model_name)()

def create_regression_model(model_name):
    """Helper function to create regression models"""
    model_map = {
        'linear': LinearRegressionModel,
        'polynomial': PolynomialRegressionModel,
        'svr': SVRModel,
        'random_forest': RandomForestRegressionModel,
        'xgboost': XGBoostRegressionModel
    }
    return model_map.get(model_name)()

def create_clustering_model(model_name):
    """Helper function to create clustering models"""
    print(f"Creating clustering model: {model_name}")
    model_map = {
        'kmeans': KMeansCluster,
        'dbscan': DBSCANCluster,
        'agglomerative': AgglomerativeCluster
    }
    return model_map.get(model_name)()

@app.route('/model_results/<task>/<file_id>')
@login_required
def model_results(task, file_id):
    try:
        model_statuses = session.get('model_statuses', {})
        models_results = []

        for model_name, status in model_statuses.items():
            if status['status'] == 'complete':
                model_path = f"temp_data/models/{model_name}_{file_id}.pkl"
                if os.path.exists(model_path):
                    try:
                        with open(model_path, 'rb') as f:
                            model_data = pickle.load(f)
                            
                            metrics = model_data.get('metrics', {})
                            formatted_metrics = {}
                            
                            if metrics:
                                # Format metrics based on task type
                                if task == 'clustering':
                                    formatted_metrics = {
                                        'silhouette': float(metrics.get('silhouette', 0)),
                                        'calinski_harabasz': float(metrics.get('calinski_harabasz', 0)),
                                        'davies_bouldin': float(metrics.get('davies_bouldin', 0)),
                                        'n_clusters': int(metrics.get('n_clusters', 0)),
                                        'cluster_sizes': metrics.get('cluster_sizes', []),
                                        'noise_points': int(metrics.get('noise_points', 0)),
                                        'visualization': metrics.get('visualization')
                                    }
                                elif task == 'classification':
                                    formatted_metrics = {
                                        'accuracy': float(metrics.get('accuracy', 0)),
                                        'precision': float(metrics.get('precision', 0)),
                                        'recall': float(metrics.get('recall', 0)),
                                        'f1': float(metrics.get('f1', 0))
                                    }
                                elif task == 'regression':
                                    formatted_metrics = {
                                        'r2': float(metrics.get('r2', 0)),
                                        'mse': float(metrics.get('mse', 0)),
                                        'rmse': float(metrics.get('rmse', 0)),
                                        'mae': float(metrics.get('mae', 0))
                                    }

                                models_results.append({
                                    'id': f"{model_name}_{file_id}",
                                    'name': model_name.replace('_', ' ').title(),
                                    'metrics': formatted_metrics
                                })
                                    
                    except Exception as e:
                        print(f"Error processing model {model_name}: {str(e)}")
                        continue

        return jsonify({
            'success': True,
            'models': models_results,
            'task': task
        })

    except Exception as e:
        print(f"Error getting model results: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/process_pca', methods=['POST'])
@login_required
def process_pca():
    try:
        print("Starting PCA processing...")
        
        # Get and validate form data
        file_id = request.form.get('file_id')
        if not file_id:
            raise ValueError('No file ID provided')
            
        try:
            n_components = int(request.form.get('n_components'))
        except (TypeError, ValueError):
            raise ValueError('Invalid number of components')
            
        has_target = request.form.get('has_target') == 'true'
        target_variable = request.form.get('target_variable') if has_target else None
        
        print(f"Processing PCA with parameters: file_id={file_id}, "
              f"n_components={n_components}, has_target={has_target}, "
              f"target_variable={target_variable}")
        
        # Load and validate data
        df = load_dataframe(file_id)
        if df is None:
            raise ValueError('Could not load data')
        
        print(f"Loaded dataframe shape: {df.shape}")
        
        # Validate target variable if provided
        if target_variable and target_variable not in df.columns:
            raise ValueError(f'Target variable {target_variable} not found in dataset')
        
        # Initialize and process PCA
        pca_model = PCAModel(n_components=n_components)
        
        # Train PCA
        if not pca_model.train(df, target_column=target_variable):
            raise ValueError('Error training PCA model')
        
        # Transform data
        transformed_df = pca_model.transform(df)
        if transformed_df is None:
            raise ValueError('Error transforming data')
        
        print(f"Transformed dataframe shape: {transformed_df.shape}")
        
        # Save results
        transformed_file_id = generate_file_id()
        save_dataframe(transformed_df, transformed_file_id)
        
        model_id = f"pca_{transformed_file_id}"
        model_path = f"temp_data/models/{model_id}.pkl"
        if not pca_model.save_model(model_path):
            raise ValueError('Error saving PCA model')
            
        # Get metrics
        metrics = pca_model.get_metrics()
        
        # Store IDs in session
        session['transformed_file_id'] = transformed_file_id
        session['pca_model_id'] = model_id
        session.modified = True
        
        # Create response
        results_url = url_for('pca_results', 
                            file_id=transformed_file_id, 
                            model_id=model_id,
                            _external=True)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'model_id': model_id,
            'transformed_file_id': transformed_file_id,
            'redirect_url': results_url
        })
        
    except Exception as e:
        print(f"Error in process_pca: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/pca_results')
@login_required
def pca_results():
    try:
        file_id = request.args.get('file_id')
        model_id = request.args.get('model_id')
        
        print(f"PCA Results route - file_id: {file_id}, model_id: {model_id}")
        
        if not file_id or not model_id:
            print("Missing parameters")
            flash('Missing required parameters', 'error')
            return redirect(url_for('models'))
        
        # Load transformed data and model
        transformed_df = load_dataframe(file_id)
        if transformed_df is None:
            print("Could not load transformed data")
            flash('Could not load transformed data', 'error')
            return redirect(url_for('models'))
        
        # Load PCA model
        pca_model = PCAModel()
        model_path = f"temp_data/models/{model_id}.pkl"
        if not os.path.exists(model_path):
            print(f"Model file not found: {model_path}")
            flash('Could not find PCA model file', 'error')
            return redirect(url_for('models'))
            
        if not pca_model.load_model(model_path):
            print("Could not load PCA model")
            flash('Could not load PCA model', 'error')
            return redirect(url_for('models'))
        
        # Get metrics and ensure all required fields are present
        metrics = pca_model.get_metrics()
        if not metrics or 'cumulative_variance_ratio' not in metrics:
            print("Invalid metrics data")
            flash('Could not load PCA metrics', 'error')
            return redirect(url_for('models'))

        # Format metrics for display
        formatted_metrics = {
            'n_components': metrics['n_components'],
            'explained_variance_ratio': [float(x) * 100 for x in metrics['explained_variance_ratio']],
            'cumulative_variance_ratio': [float(x) * 100 for x in metrics['cumulative_variance_ratio']],
            'total_variance_explained': float(metrics['cumulative_variance_ratio'][-1]) * 100,
            'feature_names': metrics.get('feature_names', [])
        }
        
        print("Formatted metrics:", formatted_metrics)  # Debug print
        
        return render_template('pca_results.html',
                             data=transformed_df.head(10),
                             metrics=formatted_metrics,
                             file_id=file_id,
                             model_id=model_id)
        
    except Exception as e:
        print(f"Error in pca_results route: {str(e)}")
        traceback.print_exc()
        flash(f'Error displaying PCA results: {str(e)}', 'error')
        return redirect(url_for('models'))

@app.route('/download_transformed_data/<file_id>')
@login_required
def download_transformed_data(file_id):
    try:
        # Load the transformed data
        df = load_dataframe(file_id)
        if df is None:
            flash('Could not load transformed data', 'error')
            return redirect(url_for('pca_results', file_id=file_id))
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='pca_transformed_data.csv'
        )
        
    except Exception as e:
        flash(f'Error downloading transformed data: {str(e)}', 'error')
        return redirect(url_for('pca_results', file_id=file_id))  

@app.route('/documentation')
def documentation():
    return render_template('documentation/intro.html', active_page='intro')

@app.route('/documentation/<page>')
def documentation_page(page):
    template_path = f'documentation/{page}.html'
    return render_template(template_path, active_page=page)

@app.route('/chat-with-ai')
def chat_with_ai():
    return render_template("chat_ai.html")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

groq_client = Groq(api_key=GROQ_API_KEY)
llama_model = "llama-3.3-70b-versatile"

current_dataset = None

@app.route("/api/prompt", methods=["POST"])
def prompt():
    try:
        if "conversation" not in session:
            session["conversation"] = []

        data = request.json
        user_prompt = data.get("prompt")

        session["conversation"].append({"role": "user", "content": user_prompt})

        if not user_prompt:
            return jsonify({"error": "The 'prompt' field is required."}), 400

        if current_dataset is None:
            return jsonify({"error": "No dataset is loaded. Please upload a file."}), 400

        dataset_info = f"Columns: {', '.join(current_dataset.columns)}"

        system_control = """
        The response must be only a minimal Python code without using ``` and plt.show(). 
        Use the loaded dataset named 'current_dataset' to perform the requested operations, it is already loaded, it's not a pain to read with pd.read_csv.
        No comment and ``` , introduction or summary is required.
        If the user asks questions to see the purpose of the dataset, you must give the answer.
        Each block after a for declaration must be correctly indented by an additional level (generally 4 spaces).
        """

        final_prompt = f"{system_control}\n\nAvailable data: {dataset_info}\n\n{user_prompt}"

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": final_prompt}],
            model=llama_model,
            temperature=0.3,
        )

        response = chat_completion.choices[0].message.content.strip()

        session["conversation"].append({"role": "assistant", "content": response})

        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/execute_code", methods=["POST"])
def execute_code():
    try:
        data = request.json
        code = data.get("code")

        if not code:
            return jsonify({"error": "No code to execute"}), 400

        local_vars = {"current_dataset": current_dataset}
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            exec(code, {}, local_vars)
            output = buf.getvalue()

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png")
        img_buffer.seek(0)
        plt.close()

        file_name = "graph.png"
        file_path = os.path.join("static", file_name)
        with open(file_path, "wb") as f:
            f.write(img_buffer.getvalue())

        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        img_html = f'<img src="data:image/png;base64,{img_base64}" alt="Generated Graph" class="w-full h-auto">'

        download_link = f'<a href="/static/{file_name}" download="graph.png" style="color: blue; text-decoration: underline; font-weight: bold; font-size: 16px;">Download the graph</a>'

        result_html = f"""
        <div class="text-lg text-gray-700 mb-4">
            <strong>Code output:</strong>
            <pre class="bg-gray-100 p-3 rounded-lg overflow-x-auto">{output}</pre>
        </div>
        <div>
            {img_html}
        </div>
        <div class="mt-4">
            {download_link}
        </div>
        """
        return jsonify({"result": result_html})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/download_dataset", methods=["GET"])
def download_dataset():
    try:
        global current_dataset
        
        if current_dataset is None:
            return jsonify({"error": "No dataset loaded for download."}), 400

        output = io.BytesIO()
        current_dataset.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)

        return (
            output.getvalue(),
            200,
            {
                "Content-Disposition": "attachment; filename=modified_dataset.csv",
                "Content-Type": "text/csv",
            },
        )
    except Exception as e:
        return jsonify({"error": f"Error generating file: {str(e)}"}), 500

@app.route("/api/upload", methods=["POST"])
def upload_dataset():
    global current_dataset

    if "datasetFile" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["datasetFile"]
    if file.filename == "":
        return jsonify({"error": "The file has no name"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    try:
        try:
            current_dataset = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                current_dataset = pd.read_excel(file_path)
            except Exception as e:
                return jsonify({"error": f"Error loading the file: {str(e)}"}), 500

        return jsonify({"message": f"File {file.filename} uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error loading the file: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)