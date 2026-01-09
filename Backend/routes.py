from flask import jsonify, render_template, request, send_from_directory, send_file
from db import get_db_connection, get_latest_audio_data, insert_audio_recording
from audiodata import extract_audio_metadata
from data_loader import process_csv_file
from werkzeug.utils import secure_filename
from config import AUDIO_DIRECTORY
from datetime import datetime, date, timedelta
import datetime
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

# --- AUDIO DATA FUNCTIONS --- #

def get_audio_api():
    """
    API endpoint to retrieve the latest audio recording data, handling
    datetime to string conversion for JSON serialization.
    """
    try:
        # 1. Fetch data from DB
        data = get_latest_audio_data(limit=10) 

        data = get_latest_audio_data(limit=10) 
        # ...

        # 2. Process data for JSON serialization
        processed_data = []
        for record in data:
            # Create a copy to modify
            record_copy = dict(record) 
            
            # Convert date (DATE type) to string
            # FIX: Check against the imported 'date' class
            if 'date' in record_copy and record_copy['date'] and isinstance(record_copy['date'], date):
                record_copy['date'] = record_copy['date'].strftime('%Y-%m-%d')
            
            # Convert start_time (DATETIME type) to string
            # FIX: Check against the imported 'datetime' class
            if 'start_time' in record_copy and record_copy['start_time'] and isinstance(record_copy['start_time'], datetime):
                record_copy['start_time'] = record_copy['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                
            # Convert end_time (DATETIME type) to string
            # FIX: Check against the imported 'datetime' class
            if 'end_time' in record_copy and record_copy['end_time'] and isinstance(record_copy['end_time'], datetime):
                record_copy['end_time'] = record_copy['end_time'].strftime('%Y-%m-%d %H:%M:%S')
                
            processed_data.append(record_copy)

        # 3. Return the processed, serializable data
        return jsonify(processed_data), 200
            
    except Exception as e:
        # Catch and log any remaining server errors
        print(f"Server Error in get_audio_api: {e}")
        return jsonify({"error": "Internal Server Error", "details": "Failed to process audio data on the server."}), 500

    """API endpoint handler for /api/v1/audio."""
    """I want to create an api get to fetch audio files from the filepath provided by user"""


def insert_audio_batch_api():
    """
    API endpoint handler for /api/v1/audio/insert. 
    Triggers batch processing and insertion of audio file paths.
    """
    try:
        result = process_and_insert_audio_batch()
        
        if result['status'] == 'error':
             # Return an error status if processing failed
             return jsonify(result), 500
        
        # Success: Return the results of the batch process
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Audio Batch API Error: {e}")
        return jsonify({"status": "error", "message": f"Server processing failed: {e}"}), 500

# --- COMBINED DATA FUNCTION ---#

def get_combined_data(start_date=None, end_date=None, limit=500):
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

def upload_audio_file():
    """
    Handles POST requests to upload a single audio file from the frontend,
    saves the file, and inserts metadata into the database.
    """
    # Check if a file was sent
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400
    
    # CRITICAL: THIS LINE DEFINES THE 'file' VARIABLE
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected for uploading"}), 400
    
    # Define allowed_file (or import it if defined elsewhere)
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # The rest of your processing logic starts here:
    if file and allowed_file(file.filename):

        if not os.path.exists(AUDIO_DIRECTORY):
            os.makedirs(AUDIO_DIRECTORY, exist_ok=True)
            
        filename = secure_filename(file.filename)
        save_path = os.path.join(AUDIO_DIRECTORY, filename)
        
        try:
            # Save the file
            file.save(save_path)
            
            # Extract metadata
            metadata = extract_audio_metadata(save_path)

            if metadata and 'start_timestamp' in metadata and 'duration' in metadata:
                
                
                start_time_int = metadata['start_timestamp']
                duration = metadata['duration']
                
                # Convert the integer Unix timestamp to a Python datetime object
                start_time_dt = datetime.fromtimestamp(start_time_int)
                
                # Calculate the end time using the datetime object
                end_time_dt = start_time_dt + timedelta(seconds=duration)

                # Get the date component for the 'date' column
                date_only = start_time_dt.date()
                
                # Insert record into database
                success, db_message = insert_audio_recording(
                    date=date_only, 
                    start_time=start_time_dt, # Use converted datetime object
                    end_time=end_time_dt,     # Use calculated datetime object
                    file_path=save_path
                )
                
                if not success:
                    # DB insertion failed, raise error to trigger cleanup
                    raise Exception(f"Database insertion failed: {db_message}")

                # Full success
                return jsonify({
                    "status": "success", 
                    "message": f"File '{filename}' successfully uploaded and record created (ID: {db_message}).",
                    "path": save_path
                }), 201
    
        except Exception as e:
            # --- CRITICAL CLEANUP STEP ---
            # If an error occurred (metadata fail or DB fail), delete the saved file.
            if save_path and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                    print(f"Cleaned up file: {save_path}")
                except Exception as cleanup_e:
                    print(f"Warning: Failed to delete file during cleanup: {cleanup_e}")
            # --- END CRITICAL CLEANUP STEP ---

            # Return error response
            return jsonify({
                "status": "error", 
                "message": f"Processing failed. File was NOT saved. Details: {e}"
            }), 500
        else:
            return jsonify({"status": "error", "message": "Invalid file type. Only MP3, WAV, OGG, FLAC are allowed."}), 400


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
        cursor.execute("SELECT * FROM audiorecording WHERE id = %s", (audio_id,))
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
    return render_template('audio.html')
