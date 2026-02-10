# backend/db.py
import pymysql
import pymysql.cursors
from contextlib import contextmanager
from config import *
from utils import format_timestamp

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
            # 1. Look for existing links
            cursor.execute("SELECT weather_data_id, sensor_data_id FROM ALL_DATA WHERE timestamp = %s", (timestamp,))
            existing = cursor.fetchone()

            # 2. Decide what to keep and what to update
            # If we are replacing sensor data, we keep the weather_id from the 'existing' row
            if source_type == 'weather':
                w_id = source_id
                s_id = existing[1] if existing else None
            else:
                s_id = source_id
                w_id = existing[0] if existing else None

            # 3. REPLACE handles the cleanup automatically
            query = "REPLACE INTO ALL_DATA (timestamp, weather_data_id, sensor_data_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (timestamp, w_id, s_id))
            conn.commit()
        except Exception as e:
            print(f"Sync Error: {e}")


# ===============
# DATA INSERTION
# ===============

def insert_sensor_data(data_row):
    ts = format_timestamp(data_row.get('timestamp'))
    if not ts: 
        return False, "Invalid timestamp"
    
    with db_session() as conn:
        if not conn:
            return False, "Database connection failed."

        cursor = conn.cursor()
        # -- NEW: Changed INSERT to REPLACE
        query = "REPLACE INTO SENSOR_DATA (`timestamp`, `date`, `time`, `moisture`) VALUES (%s, %s, %s, %s)"
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
    ts = format_timestamp(data_row.get('timestamp'))
    if not ts: 
        return False, "Invalid timestamp" 
        
    with db_session() as conn:
        if not conn:
            return False, "Database connection failed."
        try: 
            cursor = conn.cursor()
            # -- NEW: Changed INSERT to REPLACE
            query = """
                REPLACE INTO WEATHER_DATA (
                    `timestamp`, `date`, `time`, in_temperature, out_temperature, 
                    in_humidity, out_humidity, wind_speed, wind_direction, daily_rain, rain_rate
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        
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
            # -- NEW: Changed INSERT to REPLACE
            query = "REPLACE INTO AUDIO_RECORDING (`date`, start_time, end_time, file_path) VALUES (%s, %s, %s, %s)"
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

def get_latest_audio_data(limit=10):
    with db_session(dict_cursor=True) as conn:
        if not conn: return []
        cursor = conn.cursor()
        query = "SELECT * FROM AUDIO_RECORDING ORDER BY start_time DESC LIMIT %s"
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    
def get_audio_entry_by_time(start_time):
    """
    Hämtar ID och filväg för en inspelning baserat på starttid.
    Används för att kolla dubbletter utan att ta bort raden.
    """
    with db_session(dict_cursor=True) as conn:
        if not conn: return None
        cursor = conn.cursor()
        query = "SELECT id, file_path FROM AUDIO_RECORDING WHERE start_time = %s"
        cursor.execute(query, (start_time,))
        return cursor.fetchone()

def update_audio_data(id, audio_metadata):
    """
    Uppdaterar en befintlig rad istället för att ta bort och skapa ny.
    Detta behåller ID:t konstant.
    """
    end_ts = format_timestamp(audio_metadata.get('end_timestamp'))
    
    with db_session() as conn:
        if not conn: return False, "DB connection failed"
        try:
            cursor = conn.cursor()
            # Uppdatera filväg och sluttid. 
            # Vi sätter också is_deleted = 0 ifall den var borttagen innan.
            query = """
                UPDATE AUDIO_RECORDING 
                SET file_path = %s, end_time = %s, is_deleted = 0
                WHERE id = %s
            """
            values = (
                audio_metadata.get('filepath'),
                end_ts['timestamp'],
                id
            )
            cursor.execute(query, values)
            conn.commit()
            return True, id
        except Exception as e:
            print(f"Audio Update Error: {e}")
            return False, str(e)

# =================
# Soft deletion
# =================

def perform_batch_delete(ids, data_type):
    with db_session() as conn:
        if not conn: return False
        cursor = conn.cursor()
        
        # Bestäm tabell och kolumn baserat på data_type från frontenden
        if data_type == 'sensor':
            table, pk = 'SENSOR_DATA', 'sensor_id'
        elif data_type == 'weather':
            table, pk = 'WEATHER_DATA', 'weather_id'
        elif data_type == 'audio': 
            table, pk = 'AUDIO_RECORDING', 'id'
        else:
            return False

        # Skapa rätt antal %s för din SQL-fråga (t.ex. %s, %s, %s)
        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {table} SET is_deleted = 1 WHERE {pk} IN ({placeholders})"
        
        try:
            # Vi skickar med hela listan med ID:n som en tuple
            cursor.execute(query, tuple(ids))
            conn.commit()
            return True
        except Exception as e:
            print(f"Database Error: {e}")
            return False

#Hide row in Sensor data
def delete_sensor_data(sensor_id):
    return perform_batch_delete([sensor_id], 'sensor')

#Hide row in weather data
def delete_weather_data(weather_id):
    with db_session() as conn:
        if not conn:
            return False
        cursor = conn.cursor()
        query="UPDATE WEATHER_DATA SET is_deleted = 1 WHERE weather_id = %s"
        cursor.execute(query,(weather_id,))
        conn.commit()

        return True
    return perform_batch_delete([weather_id],'weather')

    
#Hide row in Audio recording data 
def delete_audio_recording(id):
    return perform_batch_delete([id], 'audio') 
    
# =================
# Regret deletion
# =================

def perform_batch_regret(ids, data_type):
    with db_session() as conn:
        if not conn: return False
        cursor = conn.cursor()
        
        # Bestäm tabell och kolumn baserat på data_type från frontenden
        if data_type == 'sensor':
            table, pk = 'SENSOR_DATA', 'sensor_id'
        elif data_type == 'weather':
            table, pk = 'WEATHER_DATA', 'weather_id'
        elif data_type == 'audio': 
            table, pk = 'AUDIO_RECORDING', 'id'
        else:
            return False

        # Skapa rätt antal %s för din SQL-fråga (t.ex. %s, %s, %s)
        placeholders = ', '.join(['%s'] * len(ids))
        query = f"UPDATE {table} SET is_deleted = 0 WHERE {pk} IN ({placeholders})"
        
        try:
            # Vi skickar med hela listan med ID:n som en tuple
            cursor.execute(query, tuple(ids))
            conn.commit()
            return True
        except Exception as e:
            print(f"Database Error: {e}")
            return False

def regret_sensor_data_deletion(sensor_id):
    return perform_batch_regret([sensor_id],'sensor')

def regret_weather_data_deletion(weather_id):
    return perform_batch_regret([weather_id],'weather')
    
def regret_audio_recording_deletion(id):
    return perform_batch_regret([id], 'audio')

# =================
# Vew deleted data
# =================

def view_deleted_weather_data():
    with db_session(dict_cursor=True) as conn:
        if not conn: return []
        cursor=conn.cursor()
        query="SELECT * FROM DELETED_WEATHER"
        cursor.execute(query)
        return cursor.fetchall()
    
def view_deleted_sensor_data():
    with db_session(dict_cursor=True) as conn:
        if not conn: return []
        cursor=conn.cursor()
        query="SELECT * FROM DELETED_SENSOR"
        cursor.execute(query)
        return cursor.fetchall()
    
def view_deleted_audio_data():
    with db_session(dict_cursor=True) as conn:
        if not conn: return []
        cursor=conn.cursor()
        query="SELECT * FROM DELETED_AUDIO"
        cursor.execute(query)
        return cursor.fetchall()