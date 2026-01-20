# backend/db.py
import pymysql
import pymysql.cursors
import datetime # Needed for UNIX timestamp conversion
from contextlib import contextmanager
from config import *

# ====================
# CONNECTION HANDLING
# ====================

def get_db_connection(dict_cursor=False):
    try:
        cursor_type = pymysql.cursors.DictCursor if dict_cursor else pymysql.cursors.Cursor
        return pymysql.connect(**DB_CONFIG, cursorclass=cursor_type)
    except Exception as e:
        print(f"ERROR: Could not connect to the database. Details: {e}")
        return None

@contextmanager
def db_session(dict_cursor=False):
    """Context manager to automatically handle opening and closing connections."""
    conn = get_db_connection(dict_cursor)
    try:
        yield conn
    finally:
        if conn:
            conn.close()

def sync_all_data(timestamp, source_type, source_id):
    with db_session() as conn:
        if not conn: return
        try:
            cursor = conn.cursor()
            # Check if a record already exists for this timestamp
            cursor.execute("SELECT all_data_id FROM ALL_DATA WHERE timestamp = %s", (timestamp,))
            existing = cursor.fetchone()
            if existing:
                column = "sensor_data_id" if source_type == 'sensor' else "weather_data_id"
                cursor.execute(f"UPDATE ALL_DATA SET {column} = %s WHERE all_data_id = %s", (source_id, existing[0]))
            else:
                # Create a new record with the data we have
                if source_type == 'sensor':
                    cursor.execute("INSERT INTO ALL_DATA (timestamp, sensor_data_id) VALUES (%s, %s)", (timestamp, source_id))
                else:
                    cursor.execute("INSERT INTO ALL_DATA (timestamp, weather_data_id) VALUES (%s, %s)", (timestamp, source_id))
            conn.commit()
        except Exception as e:
            print(f"Sync Error: {e}")

# =================
# HELPER FUNCTIONS 
# =================

def format_timestamp(unix_ts):
    if not isinstance(unix_ts, (int, float)):
        return None
    dt = datetime.datetime.fromtimestamp(unix_ts)
    return {
        'timestamp':    dt.strftime('%Y-%m-%d %H:%M:%S'), 
        'date':         dt.strftime('%Y-%m-%d'),          
        'time':         dt.strftime('%H:%M:%S')           
    }

# ======================
# SENSOR DATA INSERTION
# ======================

def insert_sensor_data(data_row):
    """
    Inserts a single row of sensor data into the SENSOR_DATA table.
    Targets the columns: date, timestamp, and moisture.
    
    :param data_row: Dictionary containing 'moisture' and 'timestamp' (Unix epoch).
    :return: Tuple (success_boolean, message_or_last_insert_id)
    """
    ts = format_timestamp(data_row.get('timestamp'))
    if not ts: 
        return False, "Invalid timestamp"
    
    with db_session() as conn:
        if not conn:
            return False, "Database connection failed."

        cursor = conn.cursor()
        query = "INSERT INTO SENSOR_DATA (`timestamp`, `date`, `time`, `Moisture`) VALUES (%s, %s, %s, %s)"
        values = (ts['timestamp'], ts['date'], ts['time'], data_row.get('moisture'))
        
        try:
            cursor.execute(query, values)
            conn.commit()
            last_id = cursor.lastrowid
            sync_all_data(ts['timestamp'], 'sensor', last_id)
            return True, last_id
        except Exception as e:
            print(f"Sensor Data Insertion Error: {e}")
            return False, str(e)
 
def insert_weather_data(data_row):
    """
    Inserts a single row of weather data into the WEATHER_DATA table.
    Calculates date, time, and timestamp from the Unix epoch input.
    """
    ts = format_timestamp(data_row.get('timestamp'))
    if not ts: 
        return False, "Invalid timestamp" 
        
    with db_session() as conn:
        if not conn:
            return False, "Database connection failed."
        try: 
            cursor = conn.cursor()
            query = """
                INSERT INTO WEATHER_DATA (
                    `timestamp`, `date`, `time`, in_temperature, out_temperature, 
                    in_humidity, out_humidity, wind_speed, wind_direction, daily_rain, rain_rate
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        
            # Prepare Values (Must match the 11 column order above)
            values = ( 
                ts['timestamp'], ts['date'], ts['time'],
                data_row.get('in_temperature'), data_row.get('out_temperature'),
                data_row.get('in_humidity'), data_row.get('out_humidity'),
                data_row.get('wind_speed'), data_row.get('wind_direction'),
                data_row.get('daily_rain'), data_row.get('rain_rate')
            )
        
            cursor.execute(query, values)
            conn.commit()
            last_id = cursor.lastrowid
            sync_all_data(ts['timestamp'], 'weather', last_id)
            return True, last_id
        
        except Exception as e:
            print(f"Weather Data Insertion Error: {e}")
            return False, f"Insertion failed: {e}"
        
# ====================
# AUDDIODATA FUNCTION
# ====================

def insert_audio_data(audio_metadata):
    start_ts = format_timestamp(audio_metadata.get('start_timestamp'))
    end_ts = format_timestamp(audio_metadata.get('end_timestamp'))
    if not start_ts or not end_ts:
        return False, "Invalid start or end timestamp"

    with db_session() as conn:
        if not conn:
            return False, "Database connection failed at insert_audio_data"

        try:
            cursor = conn.cursor()
            query = "INSERT INTO AUDIO_RECORDING (`date`, start_time, end_time, file_path) VALUES (%s, %s, %s, %s)"
            values = (
                start_ts['date'], start_ts['timestamp'],
                end_ts['timestamp'], audio_metadata.get('filepath')
            )
        
            cursor.execute(query, values)
            conn.commit()
            return True, cursor.lastrowid
        except Exception as e:
            print(f"Audio Data Insertion Error: {e}")
            return False, f"Insertion failed: {e}"


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
                JOIN AUDIO_RECORDING a ON s.timestamp BETWEEN a.start_time AND a.end_time
                WHERE a.id = %s
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
                SELECT 
                    w.timestamp, w.date, w.time,
                    w.in_temperature, w.out_temperature,
                    w.in_humidity, w.out_humidity,
                    w.wind_speed, w.wind_direction,
                    w.daily_rain, w.rain_rate
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