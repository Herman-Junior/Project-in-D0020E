# backend/db.py
import pymysql
import pymysql.cursors
import datetime # Needed for UNIX timestamp conversion

# Centralized configuration for MySQL database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '031021', # Your actual password
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