from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime

from config import Config
from database.db_connection import DatabaseConnection
from services.forecast_service import ForecastService

app = Flask(__name__)
CORS(app)
config = Config()




# Initialize components
db_connection = DatabaseConnection()
forecast_service = ForecastService()

@app.route('/')
def home():
    return jsonify({
        "message": "Prophet Model API is running!",
        "endpoints": {
            "forecast": "/forecast (POST) - Generate forecasts",
            "health": "/health (GET) - API health check"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/forecast', methods=['POST'])
def generate_forecast():
    """
    Generate forecasts using the Prophet model
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
    
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000)