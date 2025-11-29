from flask import jsonify, request, send_from_directory
from db import get_db_connection 
from data_loader import process_csv_file
import pymysql.cursors
import os 
import datetime 

# --- SENSOR DATA FUNCTIONS --- #

def get_latest_sensor_data(start_date=None, end_date=None, limit=50):
    """
    Retrieves SENSOR_DATA, formatted to show ONLY YYYY-MM-DD Date, Time (HH:MM:SS),
    and Moisture. Handles Python object serialization issues.
    """
    conn = None
    
    try:
        conn = get_db_connection(dict_cursor=True)
        if not conn: return [{'error': "Database connection failed."}]
            
        cursor = conn.cursor() 
        
        # SQL Query: Selects only the three desired display fields
        query = """
            SELECT 
                DATE(`timestamp`) AS `date`,       -- Extracts DATE object from MySQL
                TIME(`timestamp`) AS `time`,        -- Extracts TIME object/string from MySQL
                moisture AS `Moisture`              -- Uses the moisture reading
            FROM `SENSOR_DATA`
        """
        
        conditions = []
        params = []
        
        # ... (Filtering logic remains the same) ...
        
        # Execution
        cursor.execute(query, params)
        raw_data = cursor.fetchall()
        
        # POST-FETCH CONVERSION: Ensures all values are JSON-serializable strings
        data = []
        for row in raw_data:
            
            # If pymysql returns a date object, format it into a YYYY-MM-DD string
            if isinstance(row.get('date'), datetime.date):
                row['date'] = row['date'].strftime('%Y-%m-%d')
            
            # If pymysql returns a timedelta object, convert it to a string
            if isinstance(row.get('time'), datetime.timedelta):
                total_seconds = int(row['time'].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                row['time'] = f"{hours:02}:{minutes:02}:{seconds:02}"
                
            data.append(row) 

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

# --- WEATHER DATA FUNCTIONS --- #

def get_latest_weather_data(start_date=None, end_date=None, limit=50):
    """Retrieves weather_data, optionally filtered by date range."""
    conn = None
    data = []
    
    try:
        conn = get_db_connection(dict_cursor=True)
        if not conn: return [{'error': "Database connection failed."}]
            
        cursor = conn.cursor() 
        
        query = "SELECT `id`, `date`, TIME(`timestamp`) AS `timestamp`, `out_temperature`, `out_humidity`, `wind_direction` FROM `weather_data`"
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

# --- UPLOAD FUNCTIONS --- #

def upload_csv_file():
    """API endpoint to handle file upload, process the CSV, and return the result."""
    
    # Check if the POST request has the file part
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400
        
    file = request.files['file']
    
    # If the user submits an empty part
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if file:
        # Define a safe temporary path to save the file
        temp_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Use a safe filename
        filename = file.filename
        filepath = os.path.join(temp_dir, filename)
        
        try:
            # 1. Save the file temporarily
            file.save(filepath)
            
            # 2. Process the file using your existing logic
            result = process_csv_file(filepath)
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({"status": "error", "message": f"Server processing failed: {e}"}), 500
        
        finally:
            # 3. IMPORTANT: Clean up the temporary file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({"status": "error", "message": "Unknown error during upload"}), 500

# Serves the static client-side HTML file
def index():
    # Get the absolute path to the directory containing routes.py (the 'backend' folder)
    root_dir = os.path.abspath(os.path.dirname(__file__))
    
    template_dir = os.path.join(root_dir, 'templates')
    
    # Tell Flask to look in the 'templates' directory for 'index.html'
    return send_from_directory(template_dir, 'index.html')