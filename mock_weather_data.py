import csv
import random
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Output filename for the Weather Data CSV
WEATHER_FILENAME = 'mock_weather_data.csv'

# Headers must match what your data_loader.py expects
WEATHER_HEADERS = [
    'timestamp', 'in_temperature', 'out_temperature', 'in_humidity', 
    'out_humidity', 'wind_speed', 'wind_direction', 'daily_rain', 'rain_rate'
]
# Possible wind directions for realism
WIND_DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

# Timestamps will increment by 60 seconds (1 minute) for each row
TIME_STEP_SECONDS = 60

# --- DATA GENERATION FUNCTION ---

def generate_weather_row(current_ts):
    """
    Generates a single row of weather data.
    Simulates realistic relationships between internal and external values.
    """
    
    # 1. Temperature Simulation
    out_temp = round(random.uniform(5.0, 25.0), 2)  # Outdoor temp: 5C to 25C
    # Indoor temp is typically warmer and more stable than outdoor
    in_temp = round(random.uniform(out_temp + 3, out_temp + 10), 2)
    
    # 2. Humidity Simulation
    out_humidity = random.randint(30, 95)
    in_humidity = random.randint(35, 60) # Indoor humidity is more controlled

    # 3. Wind/Rain Simulation
    wind_speed = round(random.uniform(0.0, 25.0), 2)
    wind_direction = random.choice(WIND_DIRECTIONS)
    
    # Rain simulation: mostly 0, with a small chance (20%) of a non-zero value
    daily_rain_value = random.choices([0.0, random.uniform(0.1, 15.0)], weights=[80, 20], k=1)[0]
    daily_rain = round(daily_rain_value, 2)
    
    # Rain rate is also mostly 0 unless there is rain
    rain_rate = 0.0
    if daily_rain > 0.5:
        rain_rate_value = random.choices([0.0, random.uniform(0.1, 3.0)], weights=[70, 30], k=1)[0]
        rain_rate = round(rain_rate_value, 2)


    return [
        int(current_ts),    # 1. timestamp
        in_temp,            # 2. in_temperature
        out_temp,           # 3. out_temperature
        in_humidity,        # 4. in_humidity
        out_humidity,       # 5. out_humidity
        wind_speed,         # 6. wind_speed
        wind_direction,     # 7. wind_direction
        daily_rain,         # 8. daily_rain
        rain_rate           # 9. rain_rate
    ]

# --- MAIN WRITER FUNCTION ---

def generate_weather_csv(num_rows):
    """
    Generates the Weather Data CSV file with the specified number of rows.
    """
    if num_rows <= 0:
        print("Number of rows must be a positive integer.")
        return

    # Calculate starting timestamp (24 hours ago)
    start_dt = datetime.now() - timedelta(days=1)
    start_ts = start_dt.timestamp()
    current_ts = start_ts

    print(f"Generating {num_rows} rows of mock weather data...")
    print(f"Data starts at: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} (Unix: {int(start_ts)})")
    
    try:
        # Open file for writing, use semicolon (;) as the delimiter
        with open(WEATHER_FILENAME, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            
            # 1. Write headers
            writer.writerow(WEATHER_HEADERS)
            
            # 2. Write data rows
            for _ in range(num_rows):
                row = generate_weather_row(current_ts)
                writer.writerow(row)
                current_ts += TIME_STEP_SECONDS # Increment time by 1 minute
        
        print(f"SUCCESS: Generated {WEATHER_FILENAME}")
        
    except Exception as e:
        print(f"ERROR: Failed to write {WEATHER_FILENAME}. Details: {e}")


# --- EXECUTION ---

if __name__ == "__main__":
    
    while True:
        try:
            # Get user input for the number of rows
            rows_input = input("Enter the number of rows for the mock weather CSV file: ")
            
            # Attempt to convert to an integer
            rows_to_generate = int(rows_input)
            
            if rows_to_generate <= 0:
                print("Please enter a positive number.")
                continue
                
            break # Exit loop if input is valid
            
        except ValueError:
            print("Invalid input. Please enter a whole number.")
            
    # Run the generation process
    generate_weather_csv(rows_to_generate)