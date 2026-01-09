# backend/db.py
import pymysql
import pymysql.cursors
import datetime # Needed for UNIX timestamp conversion
from config import *

# Centralized configuration for MySQL database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '040813', # Your actual password
    'database': 'Weather_Db'
}

def get_db_connection(dict_cursor=False):
    try:
        cursor_type = pymysql.cursors.DictCursor if dict_cursor else pymysql.cursors.Cursor
        return pymysql.connect(**DB_CONFIG, cursorclass=cursor_type)
    except Exception as e:
        print(f"ERROR: Could not connect to the database. Details: {e}")
        return None

def sync_all_data(timestamp, source_type, source_id):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Check if a record already exists for this timestamp
        cursor.execute("SELECT all_data_id FROM ALL_DATA WHERE timestamp = %s", (timestamp,))
        existing = cursor.fetchone()

        if existing:
            # Update the existing row with the new data ID
            column = "sensor_data_id" if source_type == 'sensor' else "weather_data_id"
            cursor.execute(f"UPDATE ALL_DATA SET {column} = %s WHERE all_data_id = %s", (source_id, existing[0]))
        else:
            # Create a new record with the data we have
            if source_type == 'sensor':
                cursor.execute("INSERT INTO ALL_DATA (timestamp, sensor_data_id) VALUES (%s, %s)", (timestamp, source_id))
            else:
                cursor.execute("INSERT INTO ALL_DATA (timestamp, weather_data_id) VALUES (%s, %s)", (timestamp, source_id))
        conn.commit()
    finally:
        conn.close()

# ------------------ Sensor Data Insertion ------------------ #

def insert_sensor_data(data_row):
    """
    Inserts a single row of sensor data into the SENSOR_DATA table.
    Targets the columns: date, timestamp, and moisture.
    
    :param data_row: Dictionary containing 'moisture' and 'timestamp' (Unix epoch).
    :return: Tuple (success_boolean, message_or_last_insert_id)
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed."

        cursor = conn.cursor()
        
        # --- Handle Timestamp Conversion --- #
        timestamp_value = data_row.get('timestamp')
        date_value = None 
        
        # Only change if it's a UNIX timestamp (int or float)
        if isinstance(timestamp_value, (int, float)):
            dt_object = datetime.datetime.fromtimestamp(timestamp_value)
            # Format to MySQL DATETIME
            timestamp_value = dt_object.strftime('%Y-%m-%d %H:%M:%S')
            # Extract date part for the 'Date' column
            date_value = dt_object.strftime('%Y-%m-%d')
            time_value = dt_object.strftime('%H:%M:%S')

        # SQL Query 
        query = """
            INSERT INTO SENSOR_DATA (`timestamp`, `date`, `time`, `Moisture`)
            VALUES (%s, %s, %s, %s)
        """

        # Prepare Values (Must match the order of columns in the query)
        values = ( 
            timestamp_value,
            date_value,             
            time_value,          
            data_row.get('moisture'),  # 3. Moisture (float/int)
        )
        
        cursor.execute(query, values)
        conn.commit()
        last_id = cursor.lastrowid

        sync_all_data(timestamp_value, 'sensor', last_id)

        # Returns True and the ID of the new row.
        return True, last_id
        
    except Exception as e:
        # Log the detailed error
        print(f"Sensor Data Insertion Error: {e}")
        return False, f"Insertion failed: {e}"
        
    finally:
        # Ensures the connection is closed
        if conn:
            conn.close()

def insert_weather_data(data_row):
    """
    Inserts a single row of weather data into the WEATHER_DATA table.
    Calculates date, time, and timestamp from the Unix epoch input.
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed."

        cursor = conn.cursor()
        
        # --- Handle Timestamp Conversion --- # 
        timestamp_input = data_row.get('timestamp')
        timestamp_value = None 
        date_value = None 
        time_value = None 
        
        if isinstance(timestamp_input, (int, float)):
            dt_object = datetime.datetime.fromtimestamp(timestamp_input)
            
            # Calculate all three formats
            timestamp_value = dt_object.strftime('%Y-%m-%d %H:%M:%S')
            date_value = dt_object.strftime('%Y-%m-%d')
            time_value = dt_object.strftime('%H:%M:%S') 

        # SQL Query (Uppercase table name, lowercase column names)
        query = """
            INSERT INTO WEATHER_DATA (
                `timestamp`, `date`, `time`, in_temperature, out_temperature, 
                in_humidity, out_humidity, wind_speed, wind_direction, daily_rain, rain_rate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Prepare Values (Must match the 11 column order above)
        values = ( 
            timestamp_value,
            date_value,
            time_value,
            data_row.get('in_temperature'),
            data_row.get('out_temperature'),
            data_row.get('in_humidity'),
            data_row.get('out_humidity'),
            data_row.get('wind_speed'),
            data_row.get('wind_direction'),
            data_row.get('daily_rain'),
            data_row.get('rain_rate')
        )
        
        cursor.execute(query, values)
        conn.commit()
        last_id = cursor.lastrowid

        sync_all_data(timestamp_value, 'weather', last_id)

        return True, last_id
        
    except Exception as e:
        print(f"Weather Data Insertion Error: {e}")
        return False, f"Insertion failed: {e}"
        
    finally:
        if conn:
            conn.close()

# AUDDIODATA FUNCTION

def insert_audio_data(audio_metadata):
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
        
        cursor = conn.cursor()

        # convert UNIX timecode to datetime
        start_timestamp = audio_metadata.get('start_timestamp')
        end_timestamp = audio_metadata.get('end_timestamp')

        if isinstance(start_timestamp, (int, float)):
            start_dt = datetime.datetime.fromtimestamp(start_timestamp)
            start_time = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            date_value = start_dt.strftime('%Y-%m-%d')
        else:
            return False, "Invalid start_timestamp"
        
        if isinstance(end_timestamp, (int, float)):
            end_dt = datetime.datetime.fromtimestamp(end_timestamp)
            end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return False, "Invalid end_timestamp"
        
        # SQL QUERY

        query = """
            INSERT INTO AUDIO_RECORDING (`date`, start_time, end_time, file_path)
            VALUES (%s, %s, %s, %s)
        """
        
        values = (
            date_value,
            start_time,
            end_time,
            audio_metadata.get('filepath')
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        return True, cursor.lastrowid

    except Exception as e:
        print(f"Audio Data Insertion Error: {e}")
        return False, f"Insertion failed: {e}"
        
    finally:
        if conn:
            conn.close() 

def get_sensor_data_for_audio(audio_id):
    """
    Retrieves all sensor data that falls within an audio recording's time range.
    
    :param audio_id: ID of the audio recording
    :return: List of sensor data dictionaries
    """
    conn = None
    try:
        conn = get_db_connection(dict_cursor=True)
        if not conn:
            return []

        cursor = conn.cursor()
        
        # Query to get sensor data within the audio recording period
        query = """
            SELECT 
                s.timestamp,
                s.date,
                s.time,
                s.moisture
            FROM SENSOR_DATA s
            JOIN audiorecording a ON s.timestamp BETWEEN a.start_time AND a.end_time
            WHERE a.id = %s
            ORDER BY s.timestamp ASC
        """
        
        cursor.execute(query, (audio_id,))
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Error querying sensor data for audio: {e}")
        return []
        
    finally:
        if conn:
            conn.close()

def get_weather_data_for_audio(audio_id):
    """
    Retrieves all weather data that falls within an audio recording's time range.
    
    :param audio_id: ID of the audio recording
    :return: List of weather data dictionaries
    """
    conn = None
    try:
        conn = get_db_connection(dict_cursor=True)
        if not conn:
            return []

        cursor = conn.cursor()
        
        query = """
            SELECT 
                w.timestamp,
                w.date,
                w.time,
                w.in_temperature,
                w.out_temperature,
                w.in_humidity,
                w.out_humidity,
                w.wind_speed,
                w.wind_direction,
                w.daily_rain,
                w.rain_rate
            FROM WEATHER_DATA w
            JOIN audiorecording a ON w.timestamp BETWEEN a.start_time AND a.end_time
            WHERE a.id = %s
            ORDER BY w.timestamp ASC
        """
        
        cursor.execute(query, (audio_id,))
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Error querying weather data for audio: {e}")
        return []
        
    finally:
        if conn:
            conn.close()
