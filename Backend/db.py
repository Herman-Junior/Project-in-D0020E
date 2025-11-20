# backend/db.py
import pymysql

# Centralized configuration for your MySQL database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '031021', # Your actual password
    'database': 'Weather_Db'
}

def get_db_connection():
    """
    Establishes a new database connection using the centralized config.
    """
    try:
        # ** unpacks the dictionary into keyword arguments
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        # In a real application, you might use Flask's logging here
        print(f"ERROR: Could not connect to the database. Details: {e}")
        return None