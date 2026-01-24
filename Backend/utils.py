# backend/utils.py
from datetime import date, datetime, timedelta
import os
import re
from tinytag import TinyTag
from config import AUDIO_DIRECTORY

def format_timestamp(unix_ts):
    if not isinstance(unix_ts, (int, float)):
        return None
    dt = datetime.fromtimestamp(unix_ts)
    return {
        'timestamp':    dt.strftime('%Y-%m-%d %H:%M:%S'), 
        'date':         dt.strftime('%Y-%m-%d'),          
        'time':         dt.strftime('%H:%M:%S')           
    }

def format_for_frontend(data):
    """Concerts DB-object to JSON-string."""
    if not data: return []
    if isinstance(data, dict): data = [data]

    for row in data:
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                row[key] = value.strftime('%Y-%m-%d %H:%M:%S' if isinstance(value, datetime) else '%Y-%m-%d')
            elif isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                row[key] = f"{total_seconds // 3600:02}:{(total_seconds % 3600) // 60:02}:{total_seconds % 60:02}"
    return data

# =================
# AUDIO PROCESSING
# =================

def is_allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_audio_metadata(file_path):
    try:
        # check if exists
        if not os.path.exists(file_path):
            print(f"File not found - {file_path}")
            return None
        
        tag = TinyTag.get(file_path)
        filename = os.path.basename(file_path)
        timestamp = None
        cleaned_name = os.path.splitext(filename)[0]
        format_pattern = r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
        # FILENAME: recording_20251030_114800_LTU
        match = re.search(format_pattern, cleaned_name)

        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            hour, minute, second = int(match.group(4)), int(match.group(5)), int(match.group(6))

            # create date and convert to unix
            date = datetime(year, month, day, hour, minute, second)
            timestamp = int(date.timestamp())
        else:
            print(f"Unable to extract filename from file: {filename}")

        return {
            'filename': filename,
            'duration': tag.duration,
            'filepath': os.path.abspath(file_path),
            'start_timestamp': timestamp,
            'end_timestamp': timestamp + int(tag.duration) if timestamp else None    
        }
    
    except Exception as e:
        print(f"Error reading audio file {file_path}: {e}")
        return None
    

def extract_batch_metadata(audio_directory=None):
    if audio_directory is None:
        audio_directory = AUDIO_DIRECTORY
    
    # define which formats are allowed
    look_for = ('.mp3', '.wav')
    metadata_list = []
    
    # check for directory
    if not os.path.isdir(audio_directory):
        print(f"Error: dir not found - {audio_directory}")
        return metadata_list
    
    for filename in os.listdir(audio_directory):
        if filename.lower().endswith(look_for):
            file_path = os.path.join(audio_directory, filename)
            metadata = extract_audio_metadata(file_path)
            if metadata:
                metadata_list.append(metadata)
    return metadata_list

