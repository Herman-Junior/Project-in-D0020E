# backend/db.py
import pymysql

import datetime # Needed for UNIX timestamp conversion

# Centralized configuration for MySQL database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '031021', # Your actual password
    'database': 'Weather_Db'
}

def get_db_connection():
    """
    Establishes a new database connection using the centralized config.
    """
    try:
        # ** unpacks the dictionary into keyword arguments
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"ERROR: Could not connect to the database. Details: {e}")
        return None

# ------------------ Sensor Data Insertion ------------------ #

def insert_sensor_data(data_row):
    """
    Inserts a single row of moisture sensor data into the SENSOR_DATA table. 
    Targets the exact two columns: (Moisture, TIMESTAMP).
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed."

        cursor = conn.cursor()
        
        # --- Handle Timestamp Conversion ---
        timestamp_value = data_row.get('timestamp')
        
        # Convert UNIX epoch to MySQL DATETIME format if it's a number
        if isinstance(timestamp_value, (int, float)):
            dt_object = datetime.datetime.fromtimestamp(timestamp_value)
            timestamp_value = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        # Else: if it's already a string, we pass it as is.
        
        # SQL Query
        query = """
            INSERT INTO SENSOR_DATA (Moisture, TIMESTAMP)
            VALUES (%s, %s)
        """

        # data_row.get('moisture', None) ensures safety. If 'moisture' is missing, 
        # it passes None, which the driver converts to SQL NULL.
        values = (             
            data_row.get('moisture', None), 
            timestamp_value                                 
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Returns True and the ID of the new row, which is useful for the linking process.
        return True, cursor.lastrowid
        
    except Exception as e:
        # Log the detailed error
        print(f"Sensor Data Insertion Error: {e}")
        return False, f"Insertion failed: {e}"
        
    finally:
        if conn:
            conn.close()

def insert_weather_data(data_row):
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed."
        
        cursor = conn.cursor()

        # Handle Timestamp Conversion
        timestamp_value = data_row.get('timestamp')
        data_value = None

        if isinstance(timestamp_value, (int, float)):
            dt_object = datetime.datetime.fromtimestamp(timestamp_value)
            # Format to MySQL DATETIME
            timestamp_value = dt_object.strftime('%Y-%m-%d %H:%M:%S')
            # Extract date part for the 'Date' column
            date_value = dt_object.strftime('%Y-%m-%d')
        # If timestamp is a string, it is assumed to be in correct DATETIME format.

        # SQL Query
        query = """
            INSERT INTO weather_data (`date`, timestamp, in_temperature, out_temperature, 
                                      in_humidity, out_humidity, wind_speed, 
                                      wind_direction, daily_rain, rain_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Prepare Values (Using .get() ensures missing keys default to None/NULL)
        values = (
            date_value,                                           # date
            timestamp_value,                                      # timestamp
            data_row.get('in_temperature', None),                 # in_temperature
            data_row.get('out_temperature', None),                # out_temperature
            data_row.get('in_humidity', None),                    # in_humidity
            data_row.get('out_humidity', None),                   # out_humidity
            data_row.get('wind_speed', None),                     # wind_speed
            data_row.get('wind_direction', None),                 # wind_direction
            data_row.get('daily_rain', None),                     # daily_rain
            data_row.get('rain_rate', None)                       # rain_rate
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