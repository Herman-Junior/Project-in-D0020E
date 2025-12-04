# backend/db.py
import pymysql
import pymysql.cursors
import datetime # Needed for UNIX timestamp conversion

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
        
        # Returns True and the ID of the new row.
        return True, cursor.lastrowid
        
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
        return True, cursor.lastrowid
        
    except Exception as e:
        print(f"Weather Data Insertion Error: {e}")
        return False, f"Insertion failed: {e}"
        
    finally:
        if conn:
            conn.close()

# ------------------ Audio Recording Insertion ------------------ #
def insert_audio_recording(date, start_time, end_time, file_path):
    """
    Inserts a single audio recording record into the audiorecording table.
    
    :param date: datetime.date object
    :param start_time: datetime.datetime object
    :param end_time: datetime.datetime object
    :param file_path: Path to the saved file
    :return: Tuple (success_boolean, message_or_last_insert_id)
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed."

        cursor = conn.cursor()
        
        query = """
            INSERT INTO audiorecording 
            (`date`, start_time, end_time, file_path)
            VALUES (%s, %s, %s, %s)
        """
        
        # MySQL/pymysql can handle Python date/datetime objects directly
        values = (
            date,
            start_time,
            end_time,
            file_path
        )
        
        cursor.execute(query, values)
        conn.commit()
        last_id = cursor.lastrowid
        
        return True, last_id
        
    except Exception as e:
        # Rollback changes if an error occurs
        if conn:
            conn.rollback()
        print(f"Database Error in insert_audio_recording: {e}")
        return False, str(e)
        
    finally:
        if conn:
            conn.close()

            

def get_latest_audio_data(limit=10):
    """
    Retrieves the latest audio recording data from the audiorecording table.
    Uses a dictionary cursor to return data with column names as keys.
    """
    conn = None
    try:
        # Use DictCursor to get results as dictionaries for easy processing
        conn = get_db_connection(dict_cursor=True) 
        if not conn:
            return []

        cursor = conn.cursor()
        
        query = """
            SELECT id, date, start_time, end_time, file_path 
            FROM audiorecording 
            ORDER BY id DESC 
            LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        data = cursor.fetchall()
        
        # Data returned here contains datetime objects
        return data
        
    except Exception as e:
        print(f"Database Error in get_latest_audio_data: {e}")
        return []
        
    finally:
        if conn:
            conn.close()