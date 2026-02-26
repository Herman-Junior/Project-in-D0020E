# backend/routes.py
from flask import jsonify, render_template, request
import os
import csv
import io
from flask import Response
from datetime import datetime



# Internal project imports
from db import (perform_batch_delete, delete_weather_data, delete_audio_recording, get_db_connection, get_latest_audio_data)
from services import (
    get_audio_environmental_data_logic,
    get_latest_sensor_data,    
    get_latest_weather_data,   
    get_combined_data,         
    handle_audio_upload_logic
)
from data_loader import process_csv_file
from utils import is_allowed_file, format_for_frontend


# --- SENSOR DATA FUNCTIONS --- #

def get_sensor_api():
    """API endpoint handler for /api/v1/sensors."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    sensor_data = get_latest_sensor_data(start_date, end_date, start_time, end_time, limit=100)
    
    if sensor_data and 'error' in sensor_data[0]:
        return jsonify({'error': sensor_data[0]['error']}), 500
        
    # Success: Convert Python list of dicts to JSON
    return jsonify(sensor_data)

def get_weather_api():
    
    """API endpoint handler for /api/v1/weather."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    weather_data = get_latest_weather_data(start_date, end_date, start_time, end_time, limit=100)
    
    if weather_data and 'error' in weather_data[0]:
        return jsonify({'error': weather_data[0]['error']}), 500
        
    return jsonify(weather_data)    

def get_combined_api():
    """API endpoint handler for /api/v1/combined"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time') 
    end_time = request.args.get('end_time')    

    # Fetch data using the new DB function
    combined_data = get_combined_data(start_date, end_date, start_time, end_time, limit=200)
    
    # Error Handling
    if combined_data and 'error' in combined_data[0]:
        return jsonify({'error': combined_data[0]['error']}), 500
        
    return jsonify(combined_data)

# --- AUDIO DATA FUNCTIONS --- #

def get_audio_api():
    """
    Handles the 'special' filenames by relying on the 
    utility parser and the frontend formatter.
    """
    try:
        # Get parameters from the URL query string
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        # get_latest_audio_data should return a list of dictionaries 
        # where 'date' is a datetime.date object.
        data = get_latest_audio_data(
            start_date=start_date, 
            end_date=end_date, 
            start_time=start_time, 
            end_time=end_time, 
            limit=100
        )

        # Clean up for frontend
        for record in data:
            if record.get('file_path'):
                record['filename'] = os.path.basename(record['file_path'])
        
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


#--- Delete batch API --- #
def batch_delete_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        ids = data.get('ids', [])
        data_type = data.get('type') # 'sensor' eller 'weather'

        if not ids:
            return jsonify({'error': 'No IDs selected'}), 400

        # Anropa den nya batch-funktionen i db.py
        from db import perform_batch_delete
        success = perform_batch_delete(ids, data_type)

        if success:
            return jsonify({'message': 'Successfully marked as deleted'}), 200
        else:
            return jsonify({'error': 'Database update failed'}), 500
            
    except Exception as e:
        print(f"Route error: {e}")
        return jsonify({'error': str(e)}), 500


# --- Restore API --- #
def restore_api():
    try:
        data = request.get_json()
        ids = data.get('ids')
        data_type = data.get('type')

        from db import perform_batch_regret
    
        success = perform_batch_regret(ids, data_type)
        if success:
            return jsonify({'success': success})
        else:
            return jsonify({'error': 'Database update failed'}), 400
    except Exception as e:
        print(f"Route error: {e}")
        return jsonify({'error': str(e)}), 500
    

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
    Modified to handle initial filters if provided in the URL.
    """
    # Grab filters from the URL (if they exist)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    try:
        # Use the exact same function your API uses!
        recordings = get_latest_audio_data(
            start_date=start_date, 
            end_date=end_date, 
            start_time=start_time, 
            end_time=end_time, 
            limit=100
        )

        # Clean up filenames and format dates
        for record in recordings:
            if record.get('file_path'):
                record['filename'] = os.path.basename(record['file_path'])
            
            # Use your helper or manual format to ensure 
            # the HTML template can read them
            if hasattr(record['date'], 'strftime'):
                record['date'] = record['date'].strftime('%Y-%m-%d')
            if hasattr(record['start_time'], 'strftime'):
                record['start_time'] = record['start_time'].strftime('%H:%M:%S')

    except Exception as e:
        print(f"Error in audio_page: {e}")
        recordings = []

    return render_template('audio.html', recordings=recordings)

def audio_details_page():
    return render_template('audio_details.html')

def trash_page():
    from db import view_deleted_audio_data, view_deleted_sensor_data, view_deleted_weather_data
    import os

    # 1. Hämta all data en gång
    audio = view_deleted_audio_data()
    weather = view_deleted_weather_data()
    sensors = view_deleted_sensor_data()

    # 2. Formatera all data (Datum och Filnamn)
    for collection in [audio, weather, sensors]:
        for item in collection:
            # Fixa tidsstämplar för timern
            if 'delete_at' in item and item['delete_at']:
                item['delete_at'] = item['delete_at'].strftime('%Y-%m-%d %H:%M:%S')
            if 'timestamp' in item and item['timestamp']:
                item['timestamp'] = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Specifikt för ljudfiler: Extrahera filnamnet från sökvägen
            if 'file_path' in item and item['file_path']:
                item['filename'] = os.path.basename(item['file_path'])

    # 3. Skicka den färdigformaterade datan till HTML-sidan
    return render_template('trashcan.html', audio=audio, weather=weather, sensors=sensors)



# function for downloading data as a csv file

def export_csv_api():
    """
    GET /api/v1/export?type=sensor|weather|combined&start_date=...&end_date=...
    Returns a CSV file download of the requested data.
    """
    data_type   = request.args.get('type', 'combined')
    start_date  = request.args.get('start_date')
    end_date    = request.args.get('end_date')
    start_time  = request.args.get('start_time')
    end_time    = request.args.get('end_time')

    # --- Fetch data using existing service functions ---
    if data_type == 'sensor':
        data = get_latest_sensor_data(start_date, end_date, start_time, end_time, limit=100000)
    elif data_type == 'weather':
        data = get_latest_weather_data(start_date, end_date, start_time, end_time, limit=100000)
    else:
        data = get_combined_data(start_date, end_date, start_time, end_time, limit=100000)

    # --- Error check ---
    if data and 'error' in data[0]:
        return jsonify({'error': data[0]['error']}), 500

    if not data:
        return jsonify({'error': 'No data found for the given filters'}), 404

    # --- Build CSV in memory ---
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    # --- Stream as a file download ---
    filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )