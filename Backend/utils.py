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

def timestamp_filter(start_date, end_date, start_time, end_time, timestamp_col='`timestamp`' ):
    """
    Centralized logic to build SQL conditions and parameters for date/time filtering.
    """
    conditions = []
    params = []

    def fix_time(t, default):
        if not t or not t.strip(): return default
        t = t.strip().rstrip(':') 
        # If user typed HH:MM (length 5), add the appropriate seconds
        if len(t) == 5: 
            return f"{t}:00" if default == "00:00:00" else f"{t}:59"
        # If user typed HH:MM:SS, return it exactly as is
        return t

    # --- UPDATED HELPER: Handles partial year inputs ---
    def fix_date(d, is_end=False):
        if not d or not d.strip(): return None
        d = d.strip()
        # If only a year is typed (4 digits), turn it into a full date
        if len(d) == 4 and d.isdigit():
            return f"{d}-12-31" if is_end else f"{d}-01-01"
        return d

    # Apply the date fixing logic
    start_date = fix_date(start_date, is_end=False)
    end_date = fix_date(end_date, is_end=True)

    # Start Filter
    if start_date:
        full_start = f"{start_date} {fix_time(start_time, '00:00:00')}"
        conditions.append(f"{timestamp_col} >= %s")
        params.append(full_start)
    elif start_time and start_time.strip():
        conditions.append(f"TIME({timestamp_col}) >= %s")
        params.append(fix_time(start_time, "00:00:00"))

    # End Filter
    if end_date:
        full_end = f"{end_date} {fix_time(end_time, '23:59:59')}"
        conditions.append(f"{timestamp_col} <= %s")
        params.append(full_end)
    elif end_time and end_time.strip():
        conditions.append(f"TIME({timestamp_col}) <= %s")
        params.append(fix_time(end_time, "23:59:59"))

    return conditions, params


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
DEFAULT_FALLBACK_DURATION = 300
def is_allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#================================
# OVERLAPPING AUDIOFILE HANDLING
#================================

DEFAULT_FALLBACK_DURATION = 300

def _get_duration(tag, file_path):
    """
    Returns the audio duration in seconds.
    Uses TinyTag's value when valid, otherwise falls back to 300s (5 min).
    """
    if tag.duration and tag.duration > 1:
        return tag.duration
    # NEW: OVERLAP - fallback: mock FLACs report 0 duration, default to 5 minutes
    print(f"Warning: tag.duration missing or too small for '{os.path.basename(file_path)}', "
        f"defaulting to {DEFAULT_FALLBACK_DURATION}s ({DEFAULT_FALLBACK_DURATION//60} min).")
    return DEFAULT_FALLBACK_DURATION

def parse_timestamp_from_filename(filename):
    cleaned = os.path.splitext(os.path.basename(filename))[0]
    match = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', cleaned)
    if match:
        y, mo, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
        h, mi, s = int(match.group(4)), int(match.group(5)), int(match.group(6))
        return datetime(y, mo, d, h, mi, s)
    return None


def extract_audio_metadata(file_path):
    try:
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
            dt = datetime(year, month, day, hour, minute, second)
            timestamp = int(dt.timestamp())
        else:
            print(f"Unable to extract filename from file: {filename}")

        # NEW: OVERLAP - use _get_duration() which defaults to 5 min for mock FLACs
        duration = _get_duration(tag, file_path)

        return {
            'filename':        filename,
            'duration':        duration,
            'filepath':        os.path.abspath(file_path),
            'start_timestamp': timestamp,
            'end_timestamp':   timestamp + int(duration) if timestamp else None
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

