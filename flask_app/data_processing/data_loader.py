import pandas as pd
from pathlib import Path
import uuid
import time
import pickle
import os
import json

class DataLoader:
    def __init__(self, temp_dir="temp_data"):
        self.supported_formats = {'.csv', '.xlsx', '.xls'}
        self.temp_dir = Path(temp_dir)
        self.metadata_dir = self.temp_dir / "metadata"
        
        # Create necessary directories
        self.temp_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)

    def allowed_file(self, filename):
        """Check if the file extension is allowed"""
        return '.' in filename and Path(filename).suffix.lower() in self.supported_formats

    def parse_file(self, file):
        """Parse uploaded file and return a pandas DataFrame"""
        try:
            filename = file.filename
            if filename.endswith('.csv'):
                # List of encodings to try
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
                
                for encoding in encodings:
                    try:
                        file.seek(0)  # Reset file pointer
                        # Try reading with different separators
                        for sep in [',', ';', '\t', '|']:
                            try:
                                df = pd.read_csv(
                                    file, 
                                    encoding=encoding, 
                                    sep=sep,
                                    on_bad_lines='skip',
                                    dtype=str  # Read all columns as string first
                                )
                                # If we successfully read the file and it has more than one column
                                if len(df.columns) > 1:
                                    # Convert numeric columns
                                    for col in df.columns:
                                        try:
                                            df[col] = pd.to_numeric(df[col], errors='ignore')
                                        except:
                                            continue
                                    return df
                            except:
                                continue
                    except:
                        continue
                raise ValueError("Unable to parse CSV file with any known encoding or separator")
                
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file, dtype=str)  # Read all columns as string first
                # Convert numeric columns
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        continue
                return df
                
        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")

    def generate_file_id(self):
        """Generate a unique file ID using timestamp and UUID"""
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}"

    def save_dataframe(self, df, file_id):
        """Save dataframe to a temporary file"""
        file_path = self.temp_dir / f"{file_id}.pkl"
        df.to_pickle(str(file_path))
        return str(file_path)

    def load_dataframe(self, file_id):
        """Load dataframe from temporary file"""
        try:
            file_path = self.temp_dir / f"{file_id}.pkl"
            if not file_path.exists():
                return None
            df = pd.read_pickle(str(file_path))
            return df
        except Exception as e:
            print(f"Error loading dataframe: {e}")
            return None

    def save_metadata(self, metadata, file_id):
        """Save metadata to a temporary file"""
        metadata_path = self.metadata_dir / f"{file_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

    def load_metadata(self, file_id):
        """Load metadata from temporary file"""
        try:
            metadata_path = self.metadata_dir / f"{file_id}.json"
            if not metadata_path.exists():
                return None
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return None

    def cleanup_old_files(self, hours=24):
        """Remove files older than specified hours"""
        current_time = time.time()
        
        # Cleanup data files
        for file_path in self.temp_dir.glob("*.pkl"):
            if current_time - file_path.stat().st_mtime > hours * 3600:
                try:
                    file_path.unlink()
                except:
                    pass

        # Cleanup metadata files
        for file_path in self.metadata_dir.glob("*.json"):
            if current_time - file_path.stat().st_mtime > hours * 3600:
                try:
                    file_path.unlink()
                except:
                    pass