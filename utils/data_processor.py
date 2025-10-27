import pandas as pd
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path

class DataProcessor:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.model_registry_path = "models/model_registry.json"
        
    def convert_json_to_csv(self, json_data):
        """
        Convert JSON data from .NET server to CSV format
        Expected JSON structure:
        [
            {
                "DateTransactionJulian": "2024-01-15",
                "NameAlpha": "COMPANY NAME",
                "State": "CA",
                "Orig_Inv_Ttl_Prod_Value": 1000.50
            },
            ...
        ]
        """
        try:
            if not json_data:
                print("❌ No data provided for conversion")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(json_data)
            
            # Validate required columns
            required_columns = ['DateTransactionJulian', 'NameAlpha', 'State', 'Orig_Inv_Ttl_Prod_Value']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Missing required columns: {missing_columns}")
                return None
            
            # Clean and validate data
            df = self._clean_data(df)
            
            if df.empty:
                print("❌ No valid data after cleaning")
                return None
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"processed_data_{timestamp}.csv"
            csv_path = self.data_dir / csv_filename
            
            # Save to CSV
            df.to_csv(csv_path, index=False)
            
            print(f"✅ Successfully converted {len(df)} records to CSV: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            print(f"❌ Error converting JSON to CSV: {str(e)}")
            return None
    
    def _clean_data(self, df):
        """Clean and validate the data"""
        try:
            original_count = len(df)
            
            # Remove rows with missing critical data
            df = df.dropna(subset=['DateTransactionJulian', 'NameAlpha', 'Orig_Inv_Ttl_Prod_Value'])
            
            # Validate date format before conversion
            df = self._validate_date_formats(df)
            
            # Convert date column to proper format - handle both "2017-04-22" and "2017-04-22T00:00:00" formats
            df['DateTransactionJulian'] = pd.to_datetime(df['DateTransactionJulian'], errors='coerce')
            
            # Remove rows with invalid dates
            invalid_dates = df['DateTransactionJulian'].isna().sum()
            if invalid_dates > 0:
                print(f"⚠️ {invalid_dates} records filtered due to invalid datetime format")
            df = df.dropna(subset=['DateTransactionJulian'])
            
            # Ensure numeric values for Orig_Inv_Ttl_Prod_Value
            df['Orig_Inv_Ttl_Prod_Value'] = pd.to_numeric(df['Orig_Inv_Ttl_Prod_Value'], errors='coerce')
            invalid_values = df['Orig_Inv_Ttl_Prod_Value'].isna().sum()
            if invalid_values > 0:
                print(f"⚠️ {invalid_values} records filtered due to invalid numeric values")
            df = df.dropna(subset=['Orig_Inv_Ttl_Prod_Value'])
            
            # Remove rows with zero or negative values
            zero_values = (df['Orig_Inv_Ttl_Prod_Value'] <= 0).sum()
            if zero_values > 0:
                print(f"⚠️ {zero_values} records filtered due to zero or negative values")
            df = df[df['Orig_Inv_Ttl_Prod_Value'] > 0]
            
            # Clean company names (remove extra spaces, standardize)
            df['NameAlpha'] = df['NameAlpha'].str.strip().str.upper()
            
            # Clean state names
            df['State'] = df['State'].str.strip().str.upper()
            
            # Remove duplicates
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                print(f"⚠️ {duplicates} duplicate records removed")
            df = df.drop_duplicates()
            
            filtered_count = original_count - len(df)
            if filtered_count > 0:
                print(f"📊 Data cleaned: {len(df)} valid records remaining ({filtered_count} filtered out)")
            else:
                print(f"📊 Data cleaned: {len(df)} valid records remaining")
            return df
            
        except Exception as e:
            print(f"❌ Error cleaning data: {str(e)}")
            return pd.DataFrame()
    
    def _validate_date_formats(self, df):
        """Validate date formats and filter out invalid ones"""
        try:
            # Check for common invalid date patterns
            invalid_patterns = [
                r'^\d{1,2}/\d{1,2}/\d{4}$',  # DD/MM/YYYY or MM/DD/YYYY
                r'^\d{1,2}-\d{1,2}-\d{4}$',  # DD-MM-YYYY or MM-DD-YYYY
                r'^\d{4}/\d{1,2}/\d{1,2}$',  # YYYY/MM/DD
                r'^\d{4}-\d{1,2}-\d{1,2}$',  # YYYY-MM-DD (this is valid, but we want to be strict)
            ]
            
            import re
            
            def is_valid_date_format(date_str):
                if pd.isna(date_str) or date_str == '' or date_str is None:
                    return False
                
                date_str = str(date_str).strip()
                
                # Check for invalid patterns
                for pattern in invalid_patterns[:-1]:  # Exclude the last pattern (YYYY-MM-DD)
                    if re.match(pattern, date_str):
                        return False
                
                # Check for valid patterns
                valid_patterns = [
                    r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
                    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',  # YYYY-MM-DDTHH:MM:SS
                    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$',  # YYYY-MM-DDTHH:MM:SS.microseconds
                ]
                
                for pattern in valid_patterns:
                    if re.match(pattern, date_str):
                        return True
                
                return False
            
            # Filter out invalid date formats
            valid_mask = df['DateTransactionJulian'].apply(is_valid_date_format)
            invalid_count = (~valid_mask).sum()
            
            if invalid_count > 0:
                print(f"⚠️ {invalid_count} records filtered due to invalid date format")
                df = df[valid_mask]
            
            return df
            
        except Exception as e:
            print(f"❌ Error validating date formats: {str(e)}")
            return df
    
    def calculate_data_hash(self, csv_path):
        """Calculate hash of the data to detect changes"""
        try:
            df = pd.read_csv(csv_path)
            
            # Create a hash based on data content (excluding order)
            # Sort by date and company to ensure consistent hashing
            df_sorted = df.sort_values(['DateTransactionJulian', 'NameAlpha'])
            
            # Convert dates to consistent string format for hashing
            df_sorted = df_sorted.copy()
            df_sorted['DateTransactionJulian'] = pd.to_datetime(df_sorted['DateTransactionJulian']).dt.strftime('%Y-%m-%d')
            
            # Create hash from key columns
            hash_data = df_sorted[['DateTransactionJulian', 'NameAlpha', 'State', 'Orig_Inv_Ttl_Prod_Value']].to_string()
            data_hash = hashlib.md5(hash_data.encode()).hexdigest()
            
            return data_hash
            
        except Exception as e:
            print(f"❌ Error calculating data hash: {str(e)}")
            return None
    
    def should_retrain_models(self, csv_path, force_retrain=False):
        """
        Determine if models should be retrained based on data changes
        """
        try:
            if force_retrain:
                print("🔄 Force retrain requested")
                return True
            
            # Calculate current data hash
            current_hash = self.calculate_data_hash(csv_path)
            if not current_hash:
                print("⚠️ Could not calculate data hash, will retrain models")
                return True
            
            # Load model registry
            registry = self._load_model_registry()
            if not registry:
                print("🔄 No existing models found, will train new models")
                return True
            
            # Check if any company in current data has different hash
            df = pd.read_csv(csv_path)
            companies = df['NameAlpha'].unique()
            
            retrain_needed = False
            for company in companies:
                if company in registry['models']:
                    stored_hash = registry['models'][company]['data_hash']
                    if stored_hash != current_hash:
                        print(f"🔄 Data changed for {company}, retraining needed")
                        retrain_needed = True
                        break
                else:
                    print(f"🔄 New company {company} found, retraining needed")
                    retrain_needed = True
                    break
            
            if not retrain_needed:
                print("⚡ No data changes detected, using existing models")
            
            return retrain_needed
            
        except Exception as e:
            print(f"❌ Error checking if retrain needed: {str(e)}")
            return True  # Default to retraining if there's an error
    
    def _load_model_registry(self):
        """Load the model registry from JSON file"""
        try:
            if os.path.exists(self.model_registry_path):
                with open(self.model_registry_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"❌ Error loading model registry: {str(e)}")
            return None
    
    def update_model_registry(self, company_name, model_path, data_hash):
        """Update the model registry with new model information"""
        try:
            registry = self._load_model_registry() or {"models": {}, "last_updated": "", "cache_hits": 0, "cache_misses": 0}
            
            registry["models"][company_name] = {
                "last_trained": datetime.now().isoformat(),
                "data_hash": data_hash,
                "model_path": model_path
            }
            registry["last_updated"] = datetime.now().isoformat()
            
            # Ensure models directory exists
            os.makedirs(os.path.dirname(self.model_registry_path), exist_ok=True)
            
            with open(self.model_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)
            
            print(f"✅ Updated model registry for {company_name}")
            
        except Exception as e:
            print(f"❌ Error updating model registry: {str(e)}")
    
    def get_model_path(self, company_name):
        """Get the path to a trained model for a company"""
        try:
            registry = self._load_model_registry()
            if registry and company_name in registry["models"]:
                model_path = registry["models"][company_name]["model_path"]
                if os.path.exists(model_path):
                    return model_path
            return None
        except Exception as e:
            print(f"❌ Error getting model path for {company_name}: {str(e)}")
            return None
    
    def validate_json_structure(self, json_data):
        """Validate the structure of incoming JSON data"""
        try:
            if not isinstance(json_data, list):
                return False, "Data must be an array"
            
            if len(json_data) == 0:
                return False, "Data array cannot be empty"
            
            # Check first record structure
            first_record = json_data[0]
            required_fields = ['DateTransactionJulian', 'NameAlpha', 'State', 'Orig_Inv_Ttl_Prod_Value']
            
            for field in required_fields:
                if field not in first_record:
                    return False, f"Missing required field: {field}"
            
            return True, "Valid structure"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
