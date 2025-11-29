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
        # 1. Open file (Inspiration: "with open(filename, 'r') as csvfile:")
        with open(filepath, mode='r', encoding='utf-8') as csvfile:
            
            # 2. Create Reader (Inspiration: "csvreader = csv.reader(csvfile)")
            # We add logic to detect comma vs semicolon
            try:
                sample = csvfile.read(1024)
                csvfile.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=',;')
                csvreader = csv.reader(csvfile, dialect=dialect)
            except:
                csvfile.seek(0)
                csvreader = csv.reader(csvfile)

            # 3. Read Header (Inspiration: "fields = next(csvreader)")
            try:
                fields = next(csvreader)
                # "Vilken typ": We check the type based on column count
                col_count = len(fields)
                print(f"Detected columns: {col_count}")
            except StopIteration:
                return {"status": "error", "message": "Empty file"}

            # 4. Check Type Logic
            # "2 mer än två anrops en weather" (If > 2 columns, call Weather)
            if col_count > 2:
                target_keys = WEATHER_KEYS
                insert_func = db.insert_weather_data
            
            # "3 mindre än 2 rows (columns) anropa sensor" (If 2 columns, call Sensor)
            else:
                target_keys = SENSOR_KEYS
                insert_func = db.insert_sensor_data

            # 5. Loop rows (Inspiration: "for row in csvreader:")
            for row in csvreader:
                # Basic cleaning
                clean_row = [x.strip() for x in row]
                
                # Make sure row matches header size
                if len(clean_row) != col_count:
                    fail_count += 1
                    continue

                # Convert List to Dictionary
                data_dict = dict(zip(target_keys, clean_row))
                
                # Convert Types & Insert
                try:
                    data_dict['timestamp'] = int(float(data_dict['timestamp']))
                    
                    # Simple conversion for other fields
                    for k in data_dict:
                        if k != 'timestamp':
                            data_dict[k] = float(data_dict[k])

                    # Call the chosen function
                    result, msg = insert_func(data_dict)
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    print(f"Row failed: {e}")
                    fail_count += 1

        return {
            "status": "completed",
            "success_count": success_count,
            "fail_count": fail_count,
            "message": "Done"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}