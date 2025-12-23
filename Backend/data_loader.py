import csv
import db 
import io

# --- DEFINED FIELD MAPPINGS ---
SENSOR_FIELDS = ['moisture', 'timestamp']
WEATHER_FIELDS = [
    'timestamp', 'in_temperature', 'out_temperature', 'in_humidity', 
    'out_humidity', 'wind_speed', 'wind_direction', 'daily_rain', 'rain_rate'
]
# ------------------------------

def process_csv_file(file_stream):
    """
    Processes CSV data directly from memory. 
    'file_stream' is the file object sent from the user's browser via Flask.
    """
    print("Started processing in-memory...")
    
    success_count = 0
    fail_count = 0
    errors = []
    total_rows = 0

    try:
        # 1. Convert the raw upload stream into a text stream the CSV reader can use
        # we decode 'utf-8-sig' to automatically handle the Excel BOM if present
        content = file_stream.read().decode("utf-8-sig")
        csvfile = io.StringIO(content)
        
        # 2. Handle Delimiters (Comma vs Semicolon)
        try:
            sample = csvfile.read(1024)
            csvfile.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=',;')
            csvreader = csv.reader(csvfile, dialect=dialect)
        except Exception:
            csvfile.seek(0)
            csvreader = csv.reader(csvfile)
        
        # 3. Read header and determine data type
        try:
            fields = next(csvreader)
            fields = [f.strip() for f in fields]
            col_count = len(fields)
            total_rows = 1
        except StopIteration:
            return {"status": "error", "message": "CSV data appears empty."}
        
        print(f"--- DEBUG: Data detected with {col_count} columns.")

        if col_count == 2:
            field_map = SENSOR_FIELDS
            insert_func = db.insert_sensor_data
            data_type = "Sensor"
        elif col_count == 9: 
            field_map = WEATHER_FIELDS
            insert_func = db.insert_weather_data
            data_type = "Weather"
        else:
            return {"status": "error", "message": f"Unsupported column count: {col_count}"}

        # 4. Loop through remaining rows
        for row in csvreader:
            total_rows += 1
            stripped_row = [v.strip() for v in row]

            if len(stripped_row) != col_count:
                fail_count += 1
                continue

            data_row = dict(zip(field_map, stripped_row))
            
            try:
                if not data_row.get('timestamp'):
                    raise ValueError("Missing timestamp")
                
                # Convert timestamp (Unix)
                data_row['timestamp'] = int(float(data_row['timestamp']))
                
                # Conversion for Sensor Data
                if col_count == 2:
                    val_key = 'moisture' if 'moisture' in data_row else 'humidity'
                    data_row[val_key] = float(data_row[val_key])
                    
                # Conversion for Weather Data
                elif col_count == 9:
                    for key in ['in_temperature', 'out_temperature', 'wind_speed', 'daily_rain', 'rain_rate']:
                        data_row[key] = float(data_row[key]) if data_row.get(key) else 0.0
                    for key in ['in_humidity', 'out_humidity']:
                        data_row[key] = int(float(data_row[key])) if data_row.get(key) else 0

                # 5. Insert into Database
                result, msg = insert_func(data_row)
                
                if result:
                    success_count += 1
                    print(f"[Row {total_rows}] SUCCESS: Processed {data_type} data.")
                else:
                    fail_count += 1
                    errors.append(f"Row {total_rows} DB Error: {msg}")
                    print(f"[Row {total_rows}] FAILED: {msg}")

            except Exception as e:
                fail_count += 1
                errors.append(f"Row {total_rows} Conversion Error: {str(e)}")

        return {
            "status": "completed",
            "success_count": success_count,
            "fail_count": fail_count,
            "total_rows_read": total_rows - 1,
            "errors": errors[:5]
        }

    except Exception as e:
        return {"status": "error", "message": f"Fatal processing error: {str(e)}"}
