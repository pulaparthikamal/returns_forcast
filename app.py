from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import hashlib
import json
from datetime import datetime

from config import Config
from database.db_connection import DatabaseConnection
from services.forecast_service import ForecastService
from utils.data_processor import DataProcessor

app = Flask(__name__)
CORS(app)
config = Config()




# Initialize components
db_connection = DatabaseConnection()
forecast_service = ForecastService()
data_processor = DataProcessor()

@app.route('/')
def home():
    return jsonify({
        "message": "Prophet Model API is running!",
        "description": "Generates forecasts for both top companies and top states with highest returns",
        "endpoints": {
            "forecast": "/forecast (POST) - Generate company and state forecasts",
            "forecast_csv": "/forecast/csv (GET) - Generate forecasts from CSV (for testing)",
            "process_data": "/process-data (POST) - Process JSON data from .NET server and generate forecasts",
            "health": "/health (GET) - API health check"
        },
        "features": {
            "company_forecasts": "Predicts top 5 companies with highest returns",
            "state_forecasts": "Predicts top 5 states with highest returns",
            "forecast_period": "6 months ahead",
            "data_sources": ["CSV", "Database"]
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/forecast', methods=['POST'])
def generate_forecast():
    """
    Generate forecasts using the Prophet model - includes both company and state forecasts
    Expected JSON payload:
    {
        "data_source": "csv" or "database",
        "top_n": 5 (optional, default=5),
        "forecast_months": 6 (optional, default=6),
        "query": "SQL query" (required if data_source is database)
    }
    """
    try:
        data = request.get_json()
        data_source = data.get('data_source', 'csv')
        top_n = data.get('top_n', 5)
        forecast_months = data.get('forecast_months', 6)
        
        result = None
        
        if data_source == 'csv':
            # Generate forecast from CSV
            result = forecast_service.generate_forecast_from_csv(
                config.SAMPLE_DATA_PATH, 
                top_n, 
                forecast_months
            )
        elif data_source == 'database':
            # Generate forecast from database
            query = data.get('query')
            if not query:
                return jsonify({"error": "SQL query is required for database source"}), 400
            
            # Connect to database
            if not db_connection.connect():
                return jsonify({"error": "Failed to connect to database"}), 500
                
            result = forecast_service.generate_forecast_from_db(
                db_connection, 
                query, 
                top_n, 
                forecast_months
            )
        else:
            return jsonify({"error": "Invalid data source. Use 'csv' or 'database'"}), 400
        
        if "error" in result:
            return jsonify(result), 500
        else:
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/forecast/csv', methods=['GET'])
def generate_forecast_csv():
    """
    Generate forecasts using default CSV data (simple GET endpoint for testing)
    Returns both company and state forecasts
    """
    try:
        result = forecast_service.generate_forecast_from_csv(
            config.SAMPLE_DATA_PATH, 
            config.TOP_COMPANIES, 
            config.FORECAST_MONTHS
        )
        
        if "error" in result:
            return jsonify(result), 500
        else:
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process-data', methods=['POST'])
def process_data_from_net():
    """
    Process JSON data from .NET server and generate forecasts
    Expected JSON payload:
    {
        "data": [
            {
                "DateTransactionJulian": "2024-01-15T00:00:00",
                "NameAlpha": "COMPANY NAME",
                "State": "CA",
                "Orig_Inv_Ttl_Prod_Value": 1000.50
            },
            ...
        ],
        "top_n": 5 (optional, default=5),
        "forecast_months": 6 (optional, default=6),
        "force_retrain": false (optional, default=false)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({"error": "No data provided in request"}), 400
        
        json_data = data.get('data', [])
        top_n = data.get('top_n', 5)
        forecast_months = data.get('forecast_months', 6)
        force_retrain = data.get('force_retrain', False)
        
        if not json_data:
            return jsonify({"error": "Empty data array provided"}), 400
        
        print(f"📊 Received {len(json_data)} records from .NET server")
        
        # Convert JSON to CSV
        csv_path = data_processor.convert_json_to_csv(json_data)
        if not csv_path:
            return jsonify({"error": "Failed to convert JSON data to CSV"}), 500
        
        print(f"✅ JSON data converted to CSV: {csv_path}")
        
        # Check if CSV file has valid data
        import pandas as pd
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                return jsonify({"error": "No valid data remaining after filtering"}), 400
            print(f"📊 Valid data records: {len(df)}")
        except Exception as e:
            return jsonify({"error": f"Failed to validate CSV data: {str(e)}"}), 500
        
        # Check if data has changed and determine if retraining is needed
        should_retrain = data_processor.should_retrain_models(csv_path, force_retrain)
        
        if should_retrain:
            print("🔄 Data has changed or force retrain requested. Retraining models...")
            # Generate forecast with retraining
            result = forecast_service.generate_forecast_from_csv(
                csv_path, 
                top_n, 
                forecast_months,
                retrain_models=True
            )
        else:
            print("⚡ Using existing trained models for prediction...")
            # Generate forecast using existing models
            result = forecast_service.generate_forecast_from_csv(
                csv_path, 
                top_n, 
                forecast_months,
                retrain_models=False
            )
        
        if "error" in result:
            return jsonify(result), 500
        else:
            # Add processing metadata
            result["processing_info"] = {
                "records_processed": len(json_data),
                "csv_path": csv_path,
                "models_retrained": should_retrain,
                "processed_at": datetime.now().isoformat()
            }
            return jsonify(result)
            
    except Exception as e:
        print(f"❌ Error processing data from .NET: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('services', exist_ok=True)
    
    print("Starting Prophet Model API...")
    print("Available endpoints:")
    print("  GET  / - API information")
    print("  GET  /health - Health check")
    print("  POST /forecast - Generate forecasts")
    print("  GET  /forecast/csv - Generate forecasts from CSV (for testing)")
    print("  POST /process-data - Process JSON data from .NET server")
    
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000)