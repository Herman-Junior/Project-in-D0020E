from flask import jsonify, render_template, request, send_from_directory
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

        # THIS IS REDUNDANT CODE PACK INTO A FUNCTION LATER!!!!!!
        if start_date:
            # Filter by date part of the main timestamp column
            conditions.append("DATE(`timestamp`) >= %s") 
            params.append(start_date)
                
        if end_date:
            conditions.append("DATE(`timestamp`) <= %s")
            params.append(end_date)
                    
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
                
        query += f" ORDER BY `timestamp` DESC LIMIT {limit}"

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
    """
    Retrieves WEATHER_DATA, handling date/time formatting and serialization issues.
    It selects all detailed weather metrics along with the date and time.
    """
    conn = None
    
    try:
        conn = get_db_connection(dict_cursor=True)
        if not conn: return [{'error': "Database connection failed."}]
            
        cursor = conn.cursor() 
        
        # 1. SQL Query: Selects all columns, explicitly aliasing date and time
        query = """
            SELECT 
                DATE(`timestamp`) AS `date`, 
                TIME(`timestamp`) AS `time`,
                in_temperature, out_temperature, 
                in_humidity, out_humidity, wind_speed, 
                wind_direction, daily_rain, rain_rate
            FROM `WEATHER_DATA`
        """
        
        conditions = []
        params = []
        
        # 2. Filtering Logic (Using the main DATETIME column for consistency)
        if start_date:
            conditions.append("DATE(`timestamp`) >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("DATE(`timestamp`) <= %s")
            params.append(end_date)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY `timestamp` DESC LIMIT {limit}"

        # Execution
        cursor.execute(query, params)
        raw_data = cursor.fetchall()
        
        # 3. POST-FETCH CONVERSION: Ensures all values are JSON-serializable strings
        data = []
        for row in raw_data:
            
            # Fix 'date' formatting (YYYY-MM-DD)
            if isinstance(row.get('date'), datetime.date):
                row['date'] = row['date'].strftime('%Y-%m-%d')
            
            # Fix 'time' timedelta object (HH:MM:SS)
            if isinstance(row.get('time'), datetime.timedelta):
                total_seconds = int(row['time'].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                row['time'] = f"{hours:02}:{minutes:02}:{seconds:02}"
                
            data.append(row)

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
    return render_template('index.html')