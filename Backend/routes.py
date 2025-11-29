from flask import jsonify, request, send_from_directory
from db import get_db_connection 
import pymysql.cursors
import os 

# --- SENSOR DATA FUNCTIONS ---

def get_latest_sensor_data(start_date=None, end_date=None, limit=50):
    """Retrieves SENSOR_DATA, optionally filtered by date range."""
    conn = None
    data = []
    
    try:
        # Establish connection with DictCursor for easy JSON conversion
        conn = get_db_connection(dict_cursor=True)
        if not conn: return [{'error': "Database connection failed."}]
            
        cursor = conn.cursor() 
        
        query = "SELECT `Moisture`, `TIMESTAMP` AS `timestamp` FROM `SENSOR_DATA`"
        conditions = []
        params = []
        
        # filtering
        if start_date:
            conditions.append("DATE(`TIMESTAMP`) >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("DATE(`TIMESTAMP`) <= %s")
            params.append(end_date)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY `TIMESTAMP` DESC LIMIT {limit}"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
    
    except Exception as e:
        print(f"Sensor Database Query Error: {e}")
        data = [{'error': f"Failed to load sensor data: {e}"}]
        
    finally:
        if conn: conn.close()
            
    return data

def get_sensor_api():
    """API endpoint handler for /api/v1/sensors."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    sensor_data = get_latest_sensor_data(start_date, end_date, limit=100)
    
    if sensor_data and 'error' in sensor_data[0]:
        return jsonify({'error': sensor_data[0]['error']}), 500
        
    # Success: Convert Python list of dicts to JSON
    return jsonify(sensor_data)

# --- WEATHER DATA FUNCTIONS ---

def get_latest_weather_data(start_date=None, end_date=None, limit=50):
    """Retrieves weather_data, optionally filtered by date range."""
    conn = None
    data = []
    
    try:
        conn = get_db_connection(dict_cursor=True)
        if not conn: return [{'error': "Database connection failed."}]
            
        cursor = conn.cursor() 
        
        query = "SELECT `id`, `date`, `timestamp` AS `timestamp`, `out_temperature`, `out_humidity`, `wind_direction` FROM `weather_data`"
        conditions = []
        params = []
        
        # Filtering for weather_data uses the existing 'date' column
        if start_date:
            conditions.append("`date` >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("`date` <= %s")
            params.append(end_date)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY `timestamp` DESC LIMIT {limit}"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
    
    except Exception as e:
        print(f"Weather Database Query Error: {e}")
        data = [{'error': f"Failed to load weather data: {e}"}]
        
    finally:
        if conn: conn.close()
            
    return data

def get_weather_api():
    """API endpoint handler for /api/v1/weather."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    weather_data = get_latest_weather_data(start_date, end_date, limit=100)
    
    if weather_data and 'error' in weather_data[0]:
        return jsonify({'error': weather_data[0]['error']}), 500
        
    return jsonify(weather_data)


# Serves the static client-side HTML file
def index():
    # Get the absolute path to the directory containing routes.py (the 'backend' folder)
    root_dir = os.path.abspath(os.path.dirname(__file__))
    
    template_dir = os.path.join(root_dir, 'templates')
    
    # Tell Flask to look in the 'templates' directory for 'index.html'
    return send_from_directory(template_dir, 'index.html')