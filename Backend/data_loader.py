# Backend/data_loader.py

import csv
import os
import db 

# Defined keys for mapping the list data to database columns
SENSOR_KEYS = ['moisture', 'timestamp']
WEATHER_KEYS = ['timestamp', 'in_temperature', 'out_temperature', 'in_humidity', 'out_humidity', 'wind_speed', 'wind_direction', 'daily_rain', 'rain_rate']

def process_csv_file(filepath):
    success_count = 0
    fail_count = 0

    if not os.path.exists(filepath):
        return {"status": "error", "message": "File not found"}

    try:
        # 1. Open file and sniff dialect (delimiter detection)
        with open(filepath, mode='r', encoding='utf-8-sig') as csvfile:
            
            # Use Sniffer to detect the delimiter (comma or semicolon)
            try:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                # Sniffer and DictReader handle header reading and mapping
                dialect = csv.Sniffer().sniff(sample, delimiters=',;')
                csvreader = csv.DictReader(csvfile, dialect=dialect)
                
                fields = csvreader.fieldnames
                col_count = len(fields)
                
            except Exception as e:
                # Fallback for empty file or complex header errors
                return {"status": "error", "message": f"Could not read CSV header or dialect: {e}"}


            # 2. Determine Insertion Function
            if col_count > 2:
                # WEATHER DATA
                insert_func = db.insert_weather_data
            elif col_count == 2:
                # SENSOR DATA
                insert_func = db.insert_sensor_data
            else:
                return {"status": "error", "message": f"Unsupported column count: {col_count}"}


            # 3. Loop Rows, Convert, and Insert
            for data_dict in csvreader:
                
                # Basic cleaning (strip whitespace from keys and values)
                data_dict = {k.strip(): v.strip() for k, v in data_dict.items() if k is not None}
                
                # Convert Types & Insert
                try:
                    
                    # --- CRITICAL: TIMESTAMP CONVERSION ---
                    timestamp_raw = data_dict.get('timestamp')
                    if timestamp_raw:
                        # Convert to number (float) first. db.py will handle the datetime object conversion.
                        data_dict['timestamp'] = float(timestamp_raw)
                    else:
                        # If timestamp is missing/empty, this row MUST be rejected 
                        # to prevent the 'timestamp cannot be null' error.
                        raise ValueError("Timestamp value is empty or missing.")
                    
                    # --- NUMERIC FIELD CONVERSION ---
                    STRING_KEYS = ['wind_direction'] 
                    
                    for k, v in data_dict.items():
                        
                        key_lower = k.lower() 
                        
                        # 1. Skip if value is empty or None
                        if not v:
                            continue
                            
                        # 2. Skip the timestamp (already converted)
                        if key_lower == 'timestamp':
                            continue
                            
                        # 3. Skip explicitly defined string fields (FIX for wind_direction)
                        if key_lower in STRING_KEYS:
                            continue
                        
                        # All remaining fields are expected to be numbers; try conversion
                        try:
                            data_dict[k] = float(v)
                        except ValueError:
                            # Catch non-numeric strings (like 'N/A', '--')
                            raise ValueError(f"Data conversion failed for column '{k}' with value '{v}'.")

                    # Call the chosen function
                    result, msg = insert_func(data_dict)
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1
                
                except Exception as e:
                    # Catch and log specific row errors (invalid timestamp, failed float conversion)
                    print(f"Row failed insertion/conversion: {e}. Row data: {data_dict}")
                    fail_count += 1

        return {
            "status": "completed",
            "success_count": success_count,
            "fail_count": fail_count,
            "message": "Done"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}