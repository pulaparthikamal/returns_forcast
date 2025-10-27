import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'prophet_db')
    DB_PORT = os.getenv('DB_PORT', '3306')
    
    # Model configuration
    SAMPLE_DATA_PATH = 'data/returns_data.csv'
    TOP_COMPANIES = 5
    FORECAST_MONTHS = 6
    
    # API configuration
    DEBUG = os.getenv('DEBUG', True)