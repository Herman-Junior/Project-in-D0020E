from flask import jsonify, render_template, request, send_from_directory
from db import get_db_connection 
from data_loader import process_csv_file
import pymysql.cursors
import os 
import datetime 
from audiodata import extract_batch_metadata
from db import insert_audio_data, get_sensor_data_for_audio,get_weather_data_for_audio

# --- SENSOR DATA FUNCTIONS --- #

def get_latest_sensor_data(start_date=None, end_date=None, limit=300):
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

def get_latest_weather_data(start_date=None, end_date=None, limit=300):
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

# --- COMBINED DATA FUNCTION ---#

def get_combined_data(start_date=None, end_date=None, limit=10000):
    conn = None
    try:
        conn = get_db_connection(dict_cursor=True)
        cursor = conn.cursor()

        # We use COALESCE(W.col, S.col) to pick whichever table has the data.
        # This ensures that even if Weather is missing, we see the Sensor's Date/Time.
        query = """
            SELECT 
                COALESCE(W.date, S.date) AS date,
                COALESCE(W.time, S.time) AS time,
                W.in_temperature, W.out_temperature, W.in_humidity, W.out_humidity, 
                W.wind_speed, W.wind_direction, W.daily_rain, W.rain_rate,
                S.moisture,
                COALESCE(W.timestamp, S.timestamp) AS sort_ts
            FROM WEATHER_DATA W
            LEFT JOIN SENSOR_DATA S ON W.timestamp = S.timestamp
            
            UNION
            
            SELECT 
                COALESCE(W.date, S.date) AS date,
                COALESCE(W.time, S.time) AS time,
                W.in_temperature, W.out_temperature, W.in_humidity, W.out_humidity, 
                W.wind_speed, W.wind_direction, W.daily_rain, W.rain_rate,
                S.moisture,
                COALESCE(W.timestamp, S.timestamp) AS sort_ts
            FROM WEATHER_DATA W
            RIGHT JOIN SENSOR_DATA S ON W.timestamp = S.timestamp
        """
        
        # Build the wrapper query for filtering and sorting
        final_query = f"SELECT * FROM ({query}) AS combined_result"
        
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("date <= %s")
            params.append(end_date)
            
        if conditions:
            final_query += " WHERE " + " AND ".join(conditions)
            
        # FIX: Removed 'W.' prefix from the order clause
        final_query += f" ORDER BY sort_ts DESC LIMIT {limit}"

        cursor.execute(final_query, params)
        raw_data = cursor.fetchall()
        
        # Serialization logic (converts DB objects to strings for the browser)
        for row in raw_data:
            if isinstance(row.get('date'), datetime.date):
                row['date'] = row['date'].strftime('%Y-%m-%d')
            if isinstance(row.get('time'), datetime.timedelta):
                total_seconds = int(row['time'].total_seconds())
                row['time'] = f"{total_seconds // 3600:02}:{(total_seconds % 3600) // 60:02}:00"
            
            # Remove the sorting helper before sending to frontend
            if 'sort_ts' in row:
                del row['sort_ts']
                
        return raw_data
    except Exception as e:
        print(f"Combined Query Error: {e}")
        return [{'error': str(e)}]
    finally:
        if conn: conn.close()

def get_combined_api():
    """API endpoint handler for /api/v1/combined"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Fetch data using the new DB function
    combined_data = get_combined_data(start_date, end_date, limit=200)
    
    # Error Handling
    if combined_data and 'error' in combined_data[0]:
        return jsonify({'error': combined_data[0]['error']}), 500
        
    return jsonify(combined_data)

# --- UPLOAD FUNCTIONS --- #

def upload_csv_file():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file"}), 400

    # We pass the 'file' object (which is a stream) 
    # instead of saving it to a folder first.
    result = process_csv_file(file) 
    
    return jsonify(result)

def upload_audio_metadata():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    from config import AUDIO_DIRECTORY
    
    # Define the destination path
    filepath = os.path.join(AUDIO_DIRECTORY, file.filename)
    
    # CRITICAL: This saves the file to your 'audio_files' folder
    file.save(filepath) 
    
    # Now process it
    from audiodata import extract_audio_metadata
    metadata = extract_audio_metadata(filepath)
    
    if metadata:
        from db import insert_audio_data
        success, result = insert_audio_data(metadata)
        return jsonify({"status": "success", "audio_id": result})
    
    return jsonify({"error": "Filename does not match required date format"}), 400

def get_audio_with_environmental_data():
    """
    API endpoint to get audio recording with linked sensor and weather data.
    Usage: /api/v1/audio/<audio_id>/environmental
    """
    audio_id = request.args.get('audio_id')
    
    if not audio_id:
        return jsonify({"error": "audio_id parameter required"}), 400
    
    try:
        conn = get_db_connection(dict_cursor=True)
        cursor = conn.cursor()
        
        # Get audio recording info
        cursor.execute("SELECT * FROM AUDIO_RECORDING WHERE id = %s", (audio_id,))
        audio = cursor.fetchone()
        conn.close()
        
        if not audio:
            return jsonify({"error": "Audio recording not found"}), 404
        
        # Get linked sensor and weather data
        sensor_data = get_sensor_data_for_audio(audio_id)
        weather_data = get_weather_data_for_audio(audio_id)
        
        # Format datetime objects for JSON
        if isinstance(audio.get('date'), datetime.date):
            audio['date'] = audio['date'].strftime('%Y-%m-%d')
        if isinstance(audio.get('start_time'), datetime.datetime):
            audio['start_time'] = audio['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(audio.get('end_time'), datetime.datetime):
            audio['end_time'] = audio['end_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "audio": audio,
            "sensor_readings": sensor_data,
            "weather_readings": weather_data,
            "sensor_count": len(sensor_data),
            "weather_count": len(weather_data)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

    # Serves the static client-side HTML file

def index():    
    return render_template('home.html')

def insert_page():
    return render_template('insert.html')

def query_page():
    return render_template('query.html')

def audio_page():
    """
    Logic for the audio management page.
    Fetches all recordings to display them in the list.
    """
    conn = None
    recordings = []
    try:
        # Use dict_cursor=True so we can access columns by name in the HTML
        conn = get_db_connection(dict_cursor=True)
        if not conn:
            return render_template('audio.html', recordings=[])

        cursor = conn.cursor()
        
        # Query matching your SQL schema
        # We fetch start_time to show the user when it was recorded
        query = "SELECT id, date, start_time, file_path FROM AUDIO_RECORDING ORDER BY start_time DESC"
        cursor.execute(query)
        recordings = cursor.fetchall()

        # Clean up data for the HTML template
        for record in recordings:
            # Extract filename from path (e.g., /path/to/file.wav -> file.wav)
            if record['file_path']:
                record['filename'] = os.path.basename(record['file_path'])
            
            # Format date and time objects to strings for clean display
            if record['date']:
                record['date'] = record['date'].strftime('%Y-%m-%d')
            if record['start_time']:
                record['start_time'] = record['start_time'].strftime('%H:%M:%S')

    except Exception as e:
        print(f"Error in audio_page logic: {e}")
    finally:
        if conn:
            conn.close()

    return render_template('audio.html', recordings=recordings)
