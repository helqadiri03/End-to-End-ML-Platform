# End-to-End ML Platform

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-lightgrey.svg)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange.svg)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Plots-blueviolet.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-green.svg)

An intuitive, full-stack, automated machine learning and exploratory data analysis (EDA) platform. This project allows users to seamlessly upload datasets, clean data, generate rich 2D/3D visualizations, and train/evaluate both supervised and unsupervised machine learning models directly from the browser.

## 🚀 Features

### 1. Automated Data Processing & Cleaning
- **Dataset Upload**: Securely upload and parse `.csv`, `.xls`, and `.xlsx` files.
- **Data Cleaning**: Automatically handle missing values, duplicates, and outliers. Manual cleaning options are also available.
- **Memory Management**: Optimized in-memory caching and session management to handle complex datasets.

### 2. Advanced Interactive Visualizations
- Generate comprehensive exploratory analysis reports.
- **2D Plots**: Correlation Heatmaps, Distribution Histograms, Box Plots, and Categorical Bar Plots.
- **3D Interactive Plots**: 3D Scatter, 3D Line, and Surface interpolation using `Plotly` and `Matplotlib`.

### 3. Comprehensive Machine Learning Hub
The platform natively supports a wide variety of algorithms:
- **Classification**: KNN, Logistic Regression, Random Forest, SVM, XGBoost, Naive Bayes.
- **Regression**: Linear, Polynomial, SVR, Random Forest Regression, XGBoost Regression.
- **Clustering**: K-Means, DBSCAN, Agglomerative Clustering.
- **Dimensionality Reduction**: Principal Component Analysis (PCA).
- **Model Evaluation**: Automatically tracks and scores model accuracy, generating downloadable `.pkl` files for production use.

### 4. PDF Reporting
- Generate and download comprehensive PDF reports of your data analysis and model performance.

## 🛠️ Architecture

This repository is built using a modern modular Flask architecture:

- **`flask_app/app.py`**: The application's main entry point, router, and configuration layer.
- **`flask_app/auth/`**: Session and user authentication modules using Flask-Login and Bcrypt.
- **`flask_app/data_processing/`**: Logic for data parsing, automated/manual cleaning, and PDF report generation.
- **`flask_app/visualization/`**: Core charting services, dynamically rendering charts using Pandas, Scipy, and Plotly.
- **`flask_app/models/`**: Extensible Object-Oriented implementations of various Scikit-Learn and XGBoost ML algorithms.

## 💻 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/helqadiri03/End-to-End-ML-Platform.git
   cd End-to-End-ML-Platform
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   cd flask_app
   python app.py
   ```

5. **Access the application:**
   Navigate to `http://localhost:5000` in your web browser.

## 🔒 Security & Data Privacy
- **Secure File Handling**: Enforces file extensions, size limits (up to 100MB), and isolated temp directories per user session.
- **Data Pruning**: An automated cron-style exit handler (`atexit`) ensures temporary datasets and models older than 24 hours are safely removed from the system.
- **Authentication**: Route protection decorators and hashed credentials ensure user environments are securely segregated.

---
*Developed with a focus on streamlining the data science lifecycle from raw data to deployable insights.*
