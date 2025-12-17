import csv
import os
import json 
import db 

# --- DEFINED FIELD MAPPINGS ---
SENSOR_FIELDS = ['moisture', 'timestamp']
WEATHER_FIELDS = [
    'timestamp', 'in_temperature', 'out_temperature', 'in_humidity', 
    'out_humidity', 'wind_speed', 'wind_direction', 'daily_rain', 'rain_rate'
]
# ------------------------------

def process_csv_file(filepath):
    """
    Reads a CSV file, determines data type, and inserts data.
    Includes deep debugging prints on failure.
    """

    print("Started processing")
    
    success_count = 0
    fail_count = 0
    errors = []
    total_rows = 0

    if not os.path.exists(filepath):
        return {"status": "error", "message": "File not found"}

    try:
        # Use csv.Sniffer to handle potential semicolon or comma delimiters
        with open(filepath, mode='r', encoding='utf-8-sig') as csvfile:
            
            try:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=',;')
                csvreader = csv.reader(csvfile, dialect=dialect)
            except Exception:
                # Fallback to comma if sniffing fails
                csvfile.seek(0)
                csvreader = csv.reader(csvfile)
            
            # Read header (first row)
            try:
                fields = next(csvreader)
                fields = [f.strip() for f in fields]
                col_count = len(fields)
                total_rows = 1
            except StopIteration:
                return {"status": "error", "message": "CSV file appears empty."}
            
            print(f"--- DEBUG: File detected with {col_count} columns.")

            # Determine field mapping
            if col_count == 2:
                field_map = SENSOR_FIELDS
                insert_func = db.insert_sensor_data
            elif col_count == 9: 
                field_map = WEATHER_FIELDS
                insert_func = db.insert_weather_data
            else:
                return {"status": "error", "message": f"Unsupported column count: {col_count}. Expected 2 or 9."}

            # Loop through remaining rows
            for row in csvreader:
                total_rows += 1
                
                stripped_row = [v.strip() for v in row]

                if len(stripped_row) != col_count:
                    msg = f"Skipping row {total_rows}: column count mismatch ({len(stripped_row)} vs {col_count})"
                    fail_count += 1
                    errors.append(msg)
                    continue

                data_row = dict(zip(field_map, stripped_row))
                result = False
                msg = ""
                
                # --- CORE PARSER LOGIC WITH DEBUGGING (FIXED) ---
                try:
                    
                    if not data_row.get('timestamp'):
                        raise ValueError("Missing timestamp value.")
                    
                    # PRINT WHAT WE ARE TRYING TO CONVERT
                    print(f"--- DEBUG: Attempting to process row {total_rows}: {data_row}") 
                    
                    # 1. Convert timestamp first
                    data_row['timestamp'] = int(float(data_row['timestamp']))
                    
                    # 2. Convert remaining fields based on type
                    if col_count == 2:
                        val_key = 'moisture'
                        if val_key not in data_row:
                            val_key = 'humidity'
                        
                        if not data_row.get(val_key):
                            raise ValueError(f"Missing or empty {val_key} value.")
                        data_row[val_key] = float(data_row[val_key])
                        
                    elif col_count == 9:
                        # Numeric fields (float)
                        for key in ['in_temperature', 'out_temperature', 'wind_speed', 'daily_rain', 'rain_rate']:
                            if not data_row.get(key):
                                data_row[key] = 0.0
                            else:
                                data_row[key] = float(data_row[key])

                        # Humidity fields (int)
                        for key in ['in_humidity', 'out_humidity']:
                            if not data_row.get(key):
                                # Use 0 as default integer value if missing
                                data_row[key] = 0 
                            else:
                                # Convert to int to match DB schema (INT)
                                data_row[key] = int(float(data_row[key])) 

                        # Wind Direction is a string and requires no conversion, so we leave it alone.

                    # 3. Call the insertion function
                    result, msg = insert_func(data_row)
                    
                except ValueError as e:
                    msg = f"Data type conversion error: {e}"
                    # PRINT RAW DATA ON FAILURE
                    print(f"!!! DEBUG FAILED VALUE: {data_row}")
                    result = False
                except Exception as e:
                    msg = f"Database insertion failure: {e}"
                    # PRINT SPECIFIC DB ERROR
                    print(f"!!! DEBUG DB ERROR: {e}")
                    result = False

                # Track success/failure
                if result:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"Row {total_rows} failed: {msg} | Data: {json.dumps(data_row)}")

        return {
            "status": "completed",
            "success_count": success_count,
            "fail_count": fail_count,
            "total_rows_read": total_rows - 1,
            "errors": errors[:5]
        }

    except Exception as e:
        return {"status": "error", "message": f"Fatal CSV processing error: {str(e)}"}

def sync_all_data(timestamp, source_type, source_id):
    """
    Checks if a matching timestamp exists in the partner table 
    and links them in the ALL_DATA table.
    """
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        if source_type == 'sensor':
            # Check if weather data exists for this timestamp
            cursor.execute("SELECT weather_id FROM WEATHER_DATA WHERE timestamp = %s", (timestamp,))
            match = cursor.fetchone()
            if match:
                cursor.execute(
                    "INSERT IGNORE INTO ALL_DATA (timestamp, weather_data_id, sensor_data_id) VALUES (%s, %s, %s)",
                    (timestamp, match[0], source_id)
                )
        else: # source_type == 'weather'
            # Check if sensor data exists for this timestamp
            cursor.execute("SELECT sensor_id FROM SENSOR_DATA WHERE timestamp = %s", (timestamp,))
            match = cursor.fetchone()
            if match:
                cursor.execute(
                    "INSERT IGNORE INTO ALL_DATA (timestamp, weather_data_id, sensor_data_id) VALUES (%s, %s, %s)",
                    (timestamp, source_id, match[0])
                )
        conn.commit()
    finally:
        conn.close()