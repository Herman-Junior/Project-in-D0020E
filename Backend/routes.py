# backend/routes.py
from flask import jsonify, render_template, request
from db import view_deleted_audio_data, view_deleted_sensor_data, view_deleted_weather_data
from datetime import timedelta, date, datetime

import os

# Internal project imports
from db import (perform_batch_delete, delete_weather_data, delete_audio_recording, get_db_connection, get_latest_audio_data)
from services import (
    get_audio_environmental_data_logic,
    get_latest_sensor_data,    
    get_latest_weather_data,   
    get_combined_data,         
    handle_audio_upload_logic,
    check_audio_overlap_logic
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

    combined_data = get_combined_data(start_date, end_date, start_time, end_time, limit=200)
    
    if combined_data and 'error' in combined_data[0]:
        return jsonify({'error': combined_data[0]['error']}), 500
        
    return jsonify(combined_data)

# --- AUDIO DATA FUNCTIONS --- #

def get_audio_api():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        data = get_latest_audio_data(
            start_date=start_date, 
            end_date=end_date, 
            start_time=start_time, 
            end_time=end_time, 
            limit=100
        )

        for record in data:
            if record.get('file_path'):
                record['filename'] = os.path.basename(record['file_path'])
        
        return jsonify(format_for_frontend(data)), 200
            
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

def get_audio_environmental_api():
    """API endpoint: /api/v1/audio/environmental?audio_id=123"""
    audio_id = request.args.get('audio_id')
    if not audio_id:
        return jsonify({"error": "audio_id parameter required"}), 400
    data = get_audio_environmental_data_logic(audio_id)
    
    if 'error' in data:
        status_code = 404 if "not found" in data['error'] else 400
        return jsonify(data), status_code
        
    return jsonify(data), 200


# ===========
# OVERLAP
# ===========

def check_audio_overlap_api():
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({"error": "filename required"}), 400
    result = check_audio_overlap_logic(data['filename'])
    return jsonify(result), 200


# --- Delete batch API --- #

def batch_delete_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        ids = data.get('ids', [])
        data_type = data.get('type')

        if not ids:
            return jsonify({'error': 'No IDs selected'}), 400

        from db import perform_batch_delete
        success = perform_batch_delete(ids, data_type)

        if success:
            return jsonify({'message': 'Successfully marked as deleted'}), 200
        else:
            return jsonify({'error': 'Database update failed'}), 500
            
    except Exception as e:
        print(f"Route error: {e}")
        return jsonify({'error': str(e)}), 500

def filter_trash_api():
    s_date = request.args.get('start_date')
    e_date = request.args.get('end_date')
    s_time = request.args.get('start_time')
    e_time = request.args.get('end_time')

    try:
        audio = view_deleted_audio_data(s_date, e_date, s_time, e_time)
        sensors = view_deleted_sensor_data(s_date, e_date, s_time, e_time)
        weather = view_deleted_weather_data(s_date, e_date, s_time, e_time)

        def format_results(results):
            for row in results:
                for key, val in row.items():
                    if isinstance(val, (datetime, date)):
                        row[key] = val.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(val, timedelta):
                        row[key] = str(val)
                if 'file_path' in row and row['file_path']:
                    row['filename'] = os.path.basename(row['file_path'])
            return results

        return jsonify({
            "audio": format_results(audio),
            "sensors": format_results(sensors),
            "weather": format_results(weather)
        })

    except Exception as e:
        print(f"Filter Error: {e}")
        return jsonify({"error": str(e)}), 500

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
    """Handles multiple CSV uploads and returns a total count."""
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({"error": "No files provided"}), 400
    
    total_success = 0
    total_fail = 0
    
    for file in files:
        if file.filename == '': continue
        result = process_csv_file(file)
        total_success += result.get('success_count', 0)
        total_fail += result.get('fail_count', 0)
        
    return jsonify({
        "success_count": total_success,
        "fail_count": total_fail,
        "status": "success"
    }), 200


def upload_audio_metadata():
    """
    Saves file and extracts metadata.
    Form fields:
        file           - the audio file
        overlap_action - "trim" (default) | "overwrite"
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']

    overlap_action = request.form.get('overlap_action', 'trim')
    if overlap_action not in ('trim', 'overwrite'):
        overlap_action = 'trim'

    success, result = handle_audio_upload_logic(file, overlap_action=overlap_action)
    if not success:
        return jsonify({"error": result}), 500

    return jsonify({
        "status":   "success",
        "audio_id": result['id'],
        "message":  "Metadata extracted, file saved",
        "overlaps": result.get('overlaps', []),
    })


# NEW: merged — supports multiple files (their change) AND overlap logic (our change)
def upload_audio_api():
    """
    Handles multiple audio uploads with overlap detection.
    Reads overlap_action from form data (set by the popup in insert.html).
    """
    files = request.files.getlist('files[]')

    # NEW: also accept single file posted as 'file' (used by overlap popup JS)
    if not files or files[0].filename == '':
        single = request.files.get('file')
        if single:
            files = [single]
        else:
            return jsonify({"status": "error", "message": "No files selected"}), 400

    # NEW: read the action chosen in the popup (overwrite or trim)
    overlap_action = request.form.get('overlap_action', 'trim')
    if overlap_action not in ('trim', 'overwrite'):
        overlap_action = 'trim'

    results = []
    errors = []

    for file in files:
        if not is_allowed_file(file.filename):
            errors.append(f"Invalid type: {file.filename}")
            continue

        # NEW: pass overlap_action to the upload logic
        success, result = handle_audio_upload_logic(file, overlap_action=overlap_action)
        if success:
            results.append(result['id'])
        else:
            errors.append(f"Failed {file.filename}: {result}")

    return jsonify({
        "status":      "success" if results else "error",
        "audio_count": len(results),
        "audio_id":    results[0] if len(results) == 1 else None,
        "audio_ids":   results,
        "message":     f"Processed {len(results)} files.",
        "errors":      errors,
        "overlaps":    [],  # NEW: per-file overlaps handled internally
    }), 201


def index():    
    return render_template('home.html')

def insert_page():
    return render_template('insert.html')

def query_page():
    return render_template('query.html')

def audio_page():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    try:
        recordings = get_latest_audio_data(
            start_date=start_date, 
            end_date=end_date, 
            start_time=start_time, 
            end_time=end_time, 
            limit=100
        )

        for record in recordings:
            if record.get('file_path'):
                record['filename'] = os.path.basename(record['file_path'])
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
    import os

    audio = view_deleted_audio_data()
    weather = view_deleted_weather_data()
    sensors = view_deleted_sensor_data()

    for collection in [audio, weather, sensors]:
        for item in collection:
            if 'delete_at' in item and item['delete_at']:
                item['delete_at'] = item['delete_at'].strftime('%Y-%m-%d %H:%M:%S')
            if 'timestamp' in item and item['timestamp']:
                item['timestamp'] = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            if 'file_path' in item and item['file_path']:
                item['filename'] = os.path.basename(item['file_path'])

    return render_template('trashcan.html', audio=audio, weather=weather, sensors=sensors)