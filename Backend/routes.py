# backend/routes.py
from flask import render_template
# Import the database function from the local db module
from .db import get_db_connection 
import pymysql.cursors

def get_latest_sensor_data(limit=5):
    """
    Actual logic to retrieve the latest sensor data from the database.
    Handles connection, querying, and closing the cursor/connection.
    """
    conn = None
    data = []
    try:
        conn = get_db_connection()
        if not conn:
            # Return an error message if connection fails
            return [{'error': "Database connection failed."}]
            
        # Use DictCursor to get results as dictionaries
        cursor = conn.cursor(pymysql.cursors.DictCursor) 
        
        # Select all columns from the Sensors table
        query = f"SELECT id, timestamp, temperature, humidity, quality FROM Sensors ORDER BY timestamp DESC LIMIT {limit}"
        cursor.execute(query)
        
        # Fetch all results
        data = cursor.fetchall()
    
    except Exception as e:
        print(f"Database Query Error: {e}")
        data = [{'error': f"Failed to load data: {e}"}]
        
    finally:
        # Always close the connection
        if conn:
            conn.close()
            
    return data

# Route handler for the root URL ('/')
def index():
    """
    The main route handler for the homepage.
    """
    # Fetch data to display on the home page
    sensor_data = get_latest_sensor_data()
    
    # Render the index.html template and pass the data
    return render_template('index.html', sensor_data=sensor_data)