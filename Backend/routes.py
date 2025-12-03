from flask import jsonify, render_template, request, send_from_directory, send_file
from db import get_db_connection 
from data_loader import process_csv_file
from werkzeug.utils import secure_filename
from config import AUDIO_DIRECTORY
import pymysql.cursors
import os 
import datetime 


def upload_audio_file():
    """
    Handles POST requests to upload a single audio file from the frontend.
    """
    # 1. Check if a file was sent
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400
    
    file = request.files['file']
    
    # 2. Check if the file is empty
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected for uploading"}), 400
    
    # Optional: Check file extension (e.g., allow .mp3, .wav)
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if file and allowed_file(file.filename):

        if not os.path.exists(AUDIO_DIRECTORY):
        # os.makedirs(..., exist_ok=True) creates the directory if it doesn't exist.
            os.makedirs(AUDIO_DIRECTORY, exist_ok=True)

        # 3. Securely save the file to the audio directory
        filename = secure_filename(file.filename)
        save_path = os.path.join(AUDIO_DIRECTORY, filename)
        
        try:
            file.save(save_path)
            
            # Optional: Directly insert metadata for the *new* file
            # from audiodata import extract_audio_metadata
            # metadata = extract_audio_metadata(save_path)
            # success, last_id = insert_audio_recording(metadata['filepath'], ...)
            
            return jsonify({
                "status": "success", 
                "message": f"File '{filename}' successfully uploaded and saved.",
                "path": save_path
            }), 201
            
        except Exception as e:
            print(f"File Save Error: {e}")
            return jsonify({"status": "error", "message": f"Failed to save file: {e}"}), 500
            
    else:
        return jsonify({"status": "error", "message": "Invalid file type. Only MP3, WAV, OGG, FLAC are allowed."}), 400


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

def get_audio_api():
    file_path = request.args.get("file_path")
    if not file_path:
        return jsonify({"error": "file_path query parameter is required"}), 400

    conn = None
    try:
        conn = get_db_connection(dict_cursor=True)
        if not conn:
            return jsonify({'error': "Database connection failed."}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM audiorecording WHERE file_path = %s", (file_path,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "File not found in database"}), 404

        # ✅ Safe path resolution
        BASE_AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_files')
        full_path = os.path.join(BASE_AUDIO_DIR, os.path.basename(row["file_path"]))

        if not os.path.exists(full_path):
            return jsonify({"error": "File not found on server"}), 404

        return send_file(full_path, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()


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