import csv
import random
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Output filename for the Sensor Data CSV
SENSOR_FILENAME = 'mock_sensor_data.csv'

# Headers must match what your data_loader.py expects (moisture, timestamp)
SENSOR_HEADERS = ['moisture', 'timestamp']

# Timestamps will increment by 60 seconds (1 minute) for each row
TIME_STEP_SECONDS = 60 

# --- DATA GENERATION FUNCTION ---

def generate_sensor_row(current_ts):
    """Generates a single row of sensor data: [moisture, timestamp]."""
    
    # Moisture values (e.g., 5.0% to 95.0% range)
    moisture = round(random.uniform(5.0, 95.0), 2)
    
    return [
        moisture,
        # Convert timestamp to a 10-digit integer (seconds since epoch)
        int(current_ts) 
    ]

# --- MAIN WRITER FUNCTION ---

def generate_sensor_csv(num_rows):
    """
    Generates the Sensor Data CSV file with the specified number of rows,
    using modern Unix timestamps starting 24 hours ago.
    """
    if num_rows <= 0:
        print("Number of rows must be a positive integer.")
        return

    # Calculate starting timestamp (24 hours ago)
    start_dt = datetime.now() - timedelta(days=1)
    start_ts = start_dt.timestamp()
    current_ts = start_ts

    print(f"Generating {num_rows} rows of mock sensor data...")
    print(f"Data starts at: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} (Unix: {int(start_ts)})")
    
    try:
        # Open file for writing, use semicolon (;) as the delimiter
        with open(SENSOR_FILENAME, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            
            # 1. Write headers
            writer.writerow(SENSOR_HEADERS)
            
            # 2. Write data rows
            for _ in range(num_rows):
                row = generate_sensor_row(current_ts)
                writer.writerow(row)
                current_ts += TIME_STEP_SECONDS # Increment time by 1 minute
        
        print(f"SUCCESS: Generated {SENSOR_FILENAME}")
        
    except Exception as e:
        print(f"ERROR: Failed to write {SENSOR_FILENAME}. Details: {e}")


# --- EXECUTION ---

if __name__ == "__main__":
    
    while True:
        try:
            # Get user input for the number of rows
            rows_input = input("Enter the number of rows for the mock sensor CSV file: ")
            
            # Attempt to convert to an integer
            rows_to_generate = int(rows_input)
            
            if rows_to_generate <= 0:
                print("Please enter a positive number.")
                continue
                
            break # Exit loop if input is valid
            
        except ValueError:
            print("Invalid input. Please enter a whole number.")
            
    # Run the generation process
    generate_sensor_csv(rows_to_generate)