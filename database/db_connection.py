import pandas as pd
from sqlalchemy import create_engine, text
from config import Config

class DatabaseConnection:
    def __init__(self):
        self.config = Config()
        self.connection_string = (
            f"mssql+pyodbc://{self.config.DB_USER}:{self.config.DB.PASSWORD}@"
            f"{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}?"
            "driver=ODBC+Driver+17+for+SQL Server&"
            "TrustServerCertificate=yes"
        )
        self.engine = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database connection established successfully")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def fetch_data(self, query, params=None):
        """Fetch data from database"""
        try:
            if not self.engine:
                self.connect()
            
            with self.engine.connect() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                    
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            print("Database connection closed")