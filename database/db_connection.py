import pandas as pd
from sqlalchemy import create_engine, text
from config import Config

class DatabaseConnection:
    def __init__(self):
        self.config = Config()
        self.connection_string = f"mysql+mysqlconnector://{self.config.DB_USER}:{self.config.DB_PASSWORD}@{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}"
        self.engine = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(self.connection_string)
            print("Database connection established successfully")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def fetch_data(self, query):
        """Fetch data from database using SQL query"""
        try:
            if not self.engine:
                self.connect()
            
            with self.engine.connect() as connection:
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