# backend/services.py
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from config import AUDIO_DIRECTORY
from db import db_session, insert_audio_data, delete_audio_by_start_time, find_overlapping_recordings, update_audio_end_time,check_overlap_by_filename_start
from utils import extract_audio_metadata, format_for_frontend, format_timestamp, timestamp_filter,  parse_timestamp_from_filename

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
            WHERE (W.is_deleted = 0 OR W.is_deleted IS NULL)
                AND (S.is_deleted = 0 OR S.is_deleted IS NULL)
            
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
            WHERE (W.is_deleted = 0 OR W.is_deleted IS NULL)
                AND (S.is_deleted = 0 OR S.is_deleted IS NULL)
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



#==================
# AUDIO OVERLAPP
#==================

def check_audio_overlap_logic(filename):
    MYSQL_FMT = "%Y-%m-%d %H:%M:%S"

    start_dt = parse_timestamp_from_filename(filename)
    if not start_dt:
        # Filename doesn't match the expected pattern -- skip check
        return {"has_overlap": False, "conflicts": []}

    rows = check_overlap_by_filename_start(start_dt.strftime(MYSQL_FMT))

    conflicts = []
    for r in rows:
        conflicts.append({
            "id":         r['id'],
            "start_time": r['start_time'].strftime(MYSQL_FMT) if hasattr(r['start_time'], 'strftime') else str(r['start_time']),
            "end_time":   r['end_time'].strftime(MYSQL_FMT)   if hasattr(r['end_time'],   'strftime') else str(r['end_time']),
            "filename":   os.path.basename(r['file_path']) if r['file_path'] else "unknown",
        })

    return {
        "has_overlap": len(conflicts) > 0,
        "conflicts":   conflicts,
    }

def _resolve_overlaps(new_start_dt, new_end_dt, action):
    MYSQL_FMT = "%Y-%m-%d %H:%M:%S"

    overlapping = find_overlapping_recordings(
        new_start_dt.strftime(MYSQL_FMT),
        new_end_dt.strftime(MYSQL_FMT),
    )
    resolutions = []

    for rec in overlapping:
        ex_id    = rec['id']
        ex_start = rec['start_time']   # datetime, from pymysql DictCursor
        ex_path  = rec['file_path']

        if ex_start <= new_start_dt:
            # Existing file started before the new one -> it is the "earlier" file
            earlier_label = "existing"
            trim_point    = new_start_dt
        else:
            # New file started before the existing one -> new file is "earlier"
            earlier_label = "new"
            trim_point    = ex_start
            new_end_dt    = min(new_end_dt, trim_point)

        if action == "overwrite":
            if earlier_label == "existing":
                # Delete the physical file
                if ex_path and os.path.exists(ex_path):
                    os.remove(ex_path)
                    print(f"Overlap overwrite: deleted '{ex_path}'")
                # Hard-delete the DB row
                with db_session() as conn:
                    if conn:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM AUDIO_RECORDING WHERE id = %s", (ex_id,))
                        conn.commit()
                detail = f"Deleted existing recording #{ex_id} from DB and disk."
            else:
                detail = "New file is the earlier one; its end_time will be clamped in DB."
        else:
            # trim -- DB only, zero file I/O
            if earlier_label == "existing":
                update_audio_end_time(ex_id, trim_point.strftime(MYSQL_FMT))
                detail = (
                    f"Existing recording #{ex_id} end_time updated to "
                    f"{trim_point.strftime('%H:%M:%S')} in DB."
                )
            else:
                detail = (
                    f"New file end_time clamped to "
                    f"{trim_point.strftime('%H:%M:%S')} in DB."
                )

        resolutions.append({
            "conflicting_id": ex_id,
            "earlier":        earlier_label,
            "action":         action,
            "detail":         detail,
        })
        print(f"Overlap resolved: {detail}")

    return resolutions, new_end_dt


def handle_audio_upload_logic(file, overlap_action="trim"):
    if not os.path.exists(AUDIO_DIRECTORY):
        os.makedirs(AUDIO_DIRECTORY, exist_ok=True)

    filename   = secure_filename(file.filename)
    final_path = os.path.join(AUDIO_DIRECTORY, filename)
    temp_path  = os.path.join(AUDIO_DIRECTORY, f"temp_{filename}")

    try:
        # 1. Save as TEMP file first to read metadata
        file.save(temp_path)

        # 2. Get start/end timestamps from file
        metadata = extract_audio_metadata(temp_path)
        if not metadata or 'start_timestamp' not in metadata:
            raise Exception("Could not read date from file.")

        # do not allow files < 1 minute
        if metadata.get('duration') and metadata['duration'] < 60:
            os.remove(temp_path)
            return False, f"File too short ({int(metadata['duration'])} seconds). Minimum duration is 1 minute."




        # Convert Unix timestamp to MySQL format (YYYY-MM-DD HH:MM:SS)
        formatted_time = format_timestamp(metadata['start_timestamp'])
        mysql_start_time = formatted_time['timestamp']

        # ---------------------------------------------------------
        # 3. CHECK DUPLICATES: "Kollar andra filer om har samma datum"
        # ---------------------------------------------------------
        old_file_path = delete_audio_by_start_time(mysql_start_time)

        if old_file_path:
            print(f"Duplicate found! Removing old file: {old_file_path}")
            if os.path.exists(old_file_path):
                os.remove(old_file_path)


        # Build mysql_end_time from metadata end_timestamp
        formatted_end  = format_timestamp(metadata["end_timestamp"])
        mysql_end_time = formatted_end["timestamp"]

        # NEW: OVERLAP - step 4: resolve any overlapping recordings
        new_start_dt = datetime.strptime(mysql_start_time, "%Y-%m-%d %H:%M:%S")
        new_end_dt   = datetime.strptime(mysql_end_time,   "%Y-%m-%d %H:%M:%S")

        overlap_results, new_end_dt = _resolve_overlaps(
            new_start_dt  = new_start_dt,
            new_end_dt    = new_end_dt,
            action        = overlap_action,
        )

        # 5. Insert into DB (end_time may have been clamped by overlap resolution)
        metadata['filepath']      = final_path
        metadata['filename']      = filename
        metadata['end_timestamp'] = int(new_end_dt.timestamp())  # NEW: OVERLAP - use resolved end_time

        success, db_result = insert_audio_data(metadata)
        if not success:
            raise Exception(db_result)

        # 6. Rename temp -> final only after DB insert succeeds
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(temp_path, final_path)

        return True, {
            "id":       db_result,
            "filename": filename,
            "overlaps": overlap_results,  # NEW: OVERLAP - empty list = no conflict
        }

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, str(e)