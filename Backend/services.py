# backend/services.py
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from config import AUDIO_DIRECTORY
from db import db_session, insert_audio_data, delete_audio_by_start_time
from utils import extract_audio_metadata, format_timestamp, timestamp_filter, format_for_frontend

# =========
# DATA GET
# =========

def get_latest_sensor_data(start_date=None, end_date=None, start_time=None, end_time=None, limit=300):
    with db_session(dict_cursor=True) as conn:
        if not conn:
            return[{'error': "Database connection failed at get_latest_sensor_data."}]
        cursor = conn.cursor()

        # SQL Query: Selects only the three desired display fields
        query = """
            SELECT 
                sensor_id,
                DATE(`timestamp`) AS `date`,
                TIME(`timestamp`) AS `time`,
                moisture AS `Moisture`
            FROM `SENSOR_DATA`
            WHERE is_deleted = 0
        """

        conditions, params = timestamp_filter(start_date, end_date, start_time, end_time)          
        if conditions:
            query += " AND " + " AND ".join(conditions)
        query += f" ORDER BY `timestamp` DESC LIMIT {limit}"

        try:
            cursor.execute(query, params)      
            return format_for_frontend(cursor.fetchall())
        except Exception as e:
            print(f"Sensor Database Query Error: {e}")
            return [{'error': f"Failed to load sensor data: {e}"}]


def get_latest_weather_data(start_date=None, end_date=None, start_time=None, end_time=None, limit=300):
    """
    Retrieves WEATHER_DATA, handling date/time formatting and serialization issues.
    It selects all detailed weather metrics along with the date and time.
    """
    with db_session(dict_cursor=True) as conn:
        if not conn:
            return [{'error': "Database connection failed at get_latest_weather_data."}]
        cursor = conn.cursor()

        query = """
            SELECT
                weather_id, 
                DATE(`timestamp`) AS `date`, TIME(`timestamp`) AS `time`,
                in_temperature, out_temperature, 
                in_humidity, out_humidity, 
                wind_speed, wind_direction, 
                daily_rain, rain_rate
            FROM `WEATHER_DATA`
            WHERE is_deleted = 0
        """

        conditions, params = timestamp_filter(start_date, end_date, start_time, end_time)          
        if conditions:
            query += " AND " + " AND ".join(conditions)
                
        query += f" ORDER BY `timestamp` DESC LIMIT {limit}"

        try:
            cursor.execute(query, params)
            return format_for_frontend(cursor.fetchall())
        except Exception as e:
            print(f"Weather Database Query Error: {e}")
            return [{'error': f"Failed to load weather data: {e}"}]


def get_combined_data(start_date=None, end_date=None, start_time=None, end_time=None, limit=10000):
    """ Combines weather and sensor data using a UNION."""
    with db_session(dict_cursor=True) as conn:
        if not conn:
            return[{'error': "Database connection failed at get_combined_data."}]
        cursor = conn.cursor()

        # We use COALESCE(W.col, S.col) to pick whichever table has the data.
        # This ensures that even if Weather is missing, we see the Sensor's Date/Time.
        subquery = """
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
        final_query = f"SELECT * FROM ({subquery}) AS combined_result"
        
        conditions, params = timestamp_filter(start_date, end_date, start_time, end_time, 'sort_ts')

        if conditions:
            final_query += " WHERE " + " AND ".join(conditions)
        
        final_query += f" ORDER BY sort_ts DESC LIMIT {limit}"

        try:
            cursor.execute(final_query, params)
            raw_data = cursor.fetchall()
            data = format_for_frontend(raw_data)

            # Clean up internal helper columns befor returning to frontend
            for row in data:
                row.pop('sort_ts', None)
            return data 

        except Exception as e:
            print(f"Combined Query Error: {e}")
            return [{'error': str(e)}]

# ==========
# AUDIO GET
# ==========

def get_sensor_data_for_audio(audio_id):
    """
    Retrieves all sensor data that falls within an audio recording's time range.
    
    :param audio_id: ID of the audio recording
    :return: List of sensor data dictionaries
    """
    with db_session(dict_cursor=True) as conn:
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT s.timestamp, s.date, s.time, s.moisture
                FROM SENSOR_DATA s
                JOIN AUDIO_RECORDING a ON a.id = %s
                WHERE s.timestamp BETWEEN a.start_time AND a.end_time
                ORDER BY s.timestamp ASC
            """
            cursor.execute(query, (audio_id,))
            return cursor.fetchall()  
        except Exception as e:
            print(f"Error querying sensor data for audio: {e}")
            return []


def get_weather_data_for_audio(audio_id):
    """
    Retrieves all weather data that falls within an audio recording's time range.
    
    :param audio_id: ID of the audio recording
    :return: List of weather data dictionaries
    """
    with db_session(dict_cursor=True) as conn:
        if not conn: return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT w.*
                FROM WEATHER_DATA w
                JOIN AUDIO_RECORDING a ON a.id = %s
                WHERE w.timestamp BETWEEN a.start_time AND a.end_time
                ORDER BY w.timestamp ASC
            """
            cursor.execute(query, (audio_id,))
            return cursor.fetchall()     
        except Exception as e:
            print(f"Error querying weather data for audio: {e}")
            return []


def get_audio_environmental_data_logic(audio_id):
    """
    Fetches a specific audio recording and all environmental data 
    captured during its duration
    """
    with db_session(dict_cursor=True) as conn:
        if not conn:
            return {"error": "DB connection failed."}
        cursor = conn.cursor()

        cursor.execute("SELECT start_time, end_time FROM AUDIO_RECORDING WHERE id = %s", (audio_id,))
        audio = cursor.fetchone()

        if not audio:
            return {"error": "Audio recroding not found"}

        # Fetch Sensor Data in that window
        cursor.execute("""
            SELECT * FROM SENSOR_DATA 
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """, (audio['start_time'], audio['end_time']))
        sensors = cursor.fetchall()

        # Fetch Weather Data in that window
        cursor.execute("""
            SELECT * FROM WEATHER_DATA 
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """, (audio['start_time'], audio['end_time']))
        weather = cursor.fetchall()

        return { 
            "sensor_data": format_for_frontend(sensors),
            "weather_data": format_for_frontend(weather)
        }

def handle_audio_upload_logic(file):
    if not os.path.exists(AUDIO_DIRECTORY):
        os.makedirs(AUDIO_DIRECTORY, exist_ok=True)

    filename = secure_filename(file.filename)
    final_path = os.path.join(AUDIO_DIRECTORY, filename)
    temp_path = os.path.join(AUDIO_DIRECTORY, f"temp_{filename}")

    try:
        # 1. Save as TEMP file first to read the date
        file.save(temp_path)

        # 2. Get the Date/Time (Metadata) from the file
        metadata = extract_audio_metadata(temp_path)
        if not metadata or 'start_timestamp' not in metadata:
            raise Exception("Could not read date from file.")

        # Convert Unix timestamp to MySQL format (YYYY-MM-DD HH:MM:SS)
        formatted_time = format_timestamp(metadata['start_timestamp'])
        mysql_start_time = formatted_time['timestamp']

        # ---------------------------------------------------------
        # 3. CHECK DUPLICATES: "Kollar andra filer om har samma datum"
        # ---------------------------------------------------------
        old_file_path = delete_audio_by_start_time(mysql_start_time)

        if old_file_path:
            print(f"Duplicate found! Removing old file: {old_file_path}")
            # Remove the OLD file from the computer folder
            if os.path.exists(old_file_path):
                os.remove(old_file_path)

        # ---------------------------------------------------------
        # 4. SAVE NEW: "Laddar upp"
        # ---------------------------------------------------------
        
        # Prepare metadata for final save
        metadata['filepath'] = final_path
        metadata['filename'] = filename
        
        # Save to Database
        success, db_result = insert_audio_data(metadata)
        if not success:
            raise Exception(db_result)

        # Rename Temp file to Final filename
        if os.path.exists(final_path):
            os.remove(final_path) # Safety check
        os.rename(temp_path, final_path)

        return True, {"id": db_result, "filename": filename}

    except Exception as e:
        # If anything fails, delete the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, str(e)