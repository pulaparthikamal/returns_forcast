import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration - Updated for SQL Server
    DB_HOST = os.getenv('DB_HOST', '192.168.1.9')
    DB_USER = os.getenv('DB_USER', 'sa')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root1234$')
    DB_NAME = os.getenv('DB_NAME', 'ReturnsRX_Key')
    DB_PORT = os.getenv('DB_PORT', '1433')  # Default SQL Server port
    
    # Model configuration
    SAMPLE_DATA_PATH = 'data/ReturnsOverview_hist_past2000_clean.csv'
    TOP_COMPANIES = 5
    FORECAST_MONTHS = 6
    
    # API configuration
    DEBUG = os.getenv('DEBUG', True)