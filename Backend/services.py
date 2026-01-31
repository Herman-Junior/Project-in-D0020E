# backend/services.py
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from config import AUDIO_DIRECTORY
from db import db_session, insert_audio_data
from utils import format_for_frontend, extract_audio_metadata

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

        conditions = []
        params = []
        if start_date:
            full_start = f"{start_date} {start_time if start_time else '00:00:00'}"
            conditions.append("`timestamp` >= %s") 
            params.append(full_start)  
        if end_date:
            full_end = f"{end_date} {end_time if end_time else '23:59:59'}"
            conditions.append("`timestamp` <= %s")
            params.append(full_end)          
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY `timestamp` DESC LIMIT {limit}"

        try:
            cursor.execute(query, params)
            raw_data = cursor.fetchall()      
            return format_for_frontend(raw_data)
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
                DATE(`timestamp`) AS `date`, TIME(`timestamp`) AS `time`,
                in_temperature, out_temperature, 
                in_humidity, out_humidity, 
                wind_speed, wind_direction, 
                daily_rain, rain_rate
            FROM `WEATHER_DATA`
        """

        conditions = []
        params = []

        # 2. Filtering Logic (Using the main DATETIME column for consistency)
        if start_date:
            full_start = f"{start_date} {start_time if start_time else '00:00:00'}"
            conditions.append("`timestamp` >= %s") 
            params.append(full_start)  
        if end_date:
            full_end = f"{end_date} {end_time if end_time else '23:59:59'}"
            conditions.append("`timestamp` <= %s")
            params.append(full_end)          
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
                
        query += f" ORDER BY `timestamp` DESC LIMIT {limit}"

        try:
            cursor.execute(query, params)
            raw_data = cursor.fetchall()
            return format_for_frontend(raw_data)

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

        # Logic for Start DateTime
        if start_date:
            # If user doesn't provide a time, default to start of day (00:00:00)
            full_start = f"{start_date} {start_time if start_time else '00:00:00'}"
            conditions.append("sort_ts >= %s")
            params.append(full_start)

        # Logic for End DateTime
        if end_date:
            # If user doesn't provide a time, default to end of day (23:59:59)
            full_end = f"{end_date} {end_time if end_time else '23:59:59'}"
            conditions.append("sort_ts <= %s")
            params.append(full_end)

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
    """
    Orchestrates: Saving file -> Extracting Metadata -> DB Insertion -> Cleanup on failure.
    """
    if not os.path.exists(AUDIO_DIRECTORY):
        os.makedirs(AUDIO_DIRECTORY, exist_ok=True)

    filename = secure_filename(file.filename)
    save_path = os.path.join(AUDIO_DIRECTORY, filename)

    try:
        # Save the physical file
        file.save(save_path)

        # Get numbers from the file using your utility
        metadata = extract_audio_metadata(save_path)

        if not metadata or 'start_timestamp' not in metadata:
            raise Exception("Metadata extraction failed. Is the filename formatted correctly?")

        # Logic: Convert metadata to DB-ready objects
        start_time_dt = datetime.fromtimestamp(metadata['start_timestamp'])
        duration = metadata.get('duration', 0)
        end_time_dt = start_time_dt + timedelta(seconds=duration)

        audio_dict = {
            'start_timestamp': metadata['start_timestamp'],
            'end_timestamp': metadata['start_timestamp'] + metadata.get('duration', 0),
            'filepath': save_path
        }

        # Save to Database
        success, db_message = insert_audio_data(audio_dict)

        if not success:
            raise Exception(f"Database insertion failed: {db_message}")

        return True, {"id": db_message, "filename": filename, "path": save_path}

    except Exception as e:
        # CRITICAL CLEANUP: If anything fails after saving, delete the file!
        if os.path.exists(save_path):
            os.remove(save_path)