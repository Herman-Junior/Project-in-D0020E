# backend/routes.py
from flask import jsonify, render_template, request
import os

# Internal project imports
from db import (
    get_db_connection)
from services import (
    get_audio_environmental_data_logic,
    get_latest_sensor_data,    
    get_latest_weather_data,   
    get_combined_data,         
    handle_audio_upload_logic
)
from data_loader import process_csv_file
from utils import is_allowed_file


# --- SENSOR DATA FUNCTIONS --- #

def get_sensor_api():
    """API endpoint handler for /api/v1/sensors."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    sensor_data = get_latest_sensor_data(start_date, end_date, limit=100)
    
    if sensor_data and 'error' in sensor_data[0]:
        return jsonify({'error': sensor_data[0]['error']}), 500
        
    # Success: Convert Python list of dicts to JSON
    return jsonify(sensor_data)

def get_weather_api():
    
    """API endpoint handler for /api/v1/weather."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    weather_data = get_latest_weather_data(start_date, end_date, limit=100)
    
    if weather_data and 'error' in weather_data[0]:
        return jsonify({'error': weather_data[0]['error']}), 500
        
    return jsonify(weather_data)    

# --- AUDIO DATA FUNCTIONS --- #

def get_audio_api():
    """
    Handles the 'special' filenames by relying on the 
    utility parser and the frontend formatter.
    """
    try:
        from db import get_latest_audio_data
        from utils import format_for_frontend
        
        # get_latest_audio_data should return a list of dictionaries 
        # where 'date' is a datetime.date object.
        data = get_latest_audio_data(limit=10) 
        
        # This one line replaces all your manual strftime loops!
        return jsonify(format_for_frontend(data)), 200
            
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


def get_audio_environmental_api():
    """
    API endpoint: /api/v1/audio/environmental?audio_id=123
    """
    audio_id = request.args.get('audio_id')
    if not audio_id:
        return jsonify({"error": "audio_id parameter required"}), 400
    # Call the service
    data = get_audio_environmental_data_logic(audio_id)
    
    # Check if the service returned an error
    if 'error' in data:
        status_code = 404 if "not found" in data['error'] else 400
        return jsonify(data), status_code
        
    return jsonify(data), 200


def get_combined_api():
    """API endpoint handler for /api/v1/combined"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Fetch data using the new DB function
    combined_data = get_combined_data(start_date, end_date, limit=200)
    
    # Error Handling
    if combined_data and 'error' in combined_data[0]:
        return jsonify({'error': combined_data[0]['error']}), 500
        
    return jsonify(combined_data)


def upload_csv_file():
    """
    Handles CSV uploads by passing the stream directly to the processor.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file"}), 400
    
    result = process_csv_file(file) 
    if result.get('success_count', 0) == 0 and result.get('fail_count', 0) > 0:
        return jsonify(result), 400
        
    return jsonify(result), 200 # Returns 200 if at least some rows succeeded

def upload_audio_metadata():
    """
    Saves file and extracts metadata
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    success, result = handle_audio_upload_logic(file)
    
    if not success:
        return jsonify({"error": result}), 500
    
    return jsonify({
        "status": "success",
        "audio_id": result['id'],
        "message": "Metadata extracted, file saved"
    })

def upload_audio_api(): 
    """
    API endpoint to handle audio uploads.
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
    
    if not is_allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file type."}), 400

    success, result = handle_audio_upload_logic(file)
    
    if not success:
        return jsonify({"status": "error", "message": result}), 500

    return jsonify({
        "status": "success", 
        "message": f"File '{result['filename']}' successfully processed.",
        "id": result['id']
    }), 201

    # Serves the static client-side HTML file

def index():    
    return render_template('home.html')

def insert_page():
    return render_template('insert.html')

def query_page():
    return render_template('query.html')

def audio_page():
    """
    Logic for the audio management page.
    Fetches all recordings to display them in the list.
    """
    conn = None
    recordings = []
    try:
        # Use dict_cursor=True so we can access columns by name in the HTML
        conn = get_db_connection(dict_cursor=True)
        if not conn:
            return render_template('audio.html', recordings=[])

        cursor = conn.cursor()
        
        # Query matching your SQL schema
        # We fetch start_time to show the user when it was recorded
        query = "SELECT id, date, start_time, file_path FROM AUDIO_RECORDING ORDER BY start_time DESC"
        cursor.execute(query)
        recordings = cursor.fetchall()

        # Clean up data for the HTML template
        for record in recordings:
            # Extract filename from path (e.g., /path/to/file.wav -> file.wav)
            if record['file_path']:
                record['filename'] = os.path.basename(record['file_path'])
            
            # Format date and time objects to strings for clean display
            if record['date']:
                record['date'] = record['date'].strftime('%Y-%m-%d')
            if record['start_time']:
                record['start_time'] = record['start_time'].strftime('%H:%M:%S')

    except Exception as e:
        print(f"Error in audio_page logic: {e}")
    finally:
        if conn:
            conn.close()

    return render_template('audio.html', recordings=recordings)

