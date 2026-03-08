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

def timestamp_filter(start_date, end_date, start_time, end_time, timestamp_col='`timestamp`'):
    conditions = []
    params = []

    def fix_time(t, default):
        if not t or not t.strip(): 
            return default
        t = t.strip().rstrip(':') 
        if len(t) == 5: # HH:MM
            return f"{t}:00" if default == "00:00:00" else f"{t}:59"
        return t

    def fix_date(d, is_end=False):
        if not d or not d.strip(): 
            return None
        d = d.strip()
        if len(d) == 4 and d.isdigit():
            return f"{d}-12-31" if is_end else f"{d}-01-01"
        return d

    # Process dates
    s_date = fix_date(start_date, is_end=False)
    e_date = fix_date(end_date, is_end=True)

    # Process times
    s_time = fix_time(start_time, "00:00:00")
    e_time = fix_time(end_time, "23:59:59")

    any_date = s_date or e_date

    if any_date:
        # A date is involved — always use full datetime comparisons to avoid
        # mixing `timestamp >= 'date time'` with `TIME(timestamp) <= 'time'`,
        # which would incorrectly bleed the time filter across all future dates.
        if s_date:
            conditions.append(f"{timestamp_col} >= %s")
            params.append(f"{s_date} {s_time}")
        if e_date:
            conditions.append(f"{timestamp_col} <= %s")
            params.append(f"{e_date} {e_time}")
    else:
        # No date provided — use TIME() for pure time-of-day filtering
        if start_time and start_time.strip():
            conditions.append(f"TIME({timestamp_col}) >= %s")
            params.append(s_time)
        if end_time and end_time.strip():
            conditions.append(f"TIME({timestamp_col}) <= %s")
            params.append(e_time)

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
    1. Uses TinyTag's value when valid (> 1s).
    2. Falls back to counting actual FLAC audio frames from the file data.
    3. Last resort: returns DEFAULT_FALLBACK_DURATION (300s).
    """
    if tag.duration and tag.duration > 1:
        return tag.duration

    # Fallback: count real FLAC frames to get actual duration
    if file_path.lower().endswith('.flac'):
        try:
            duration = _get_flac_duration_from_frames(file_path)
            if duration and duration > 1:
                print(f"Info: tag.duration was 0 for '{os.path.basename(file_path)}', "
                      f"calculated real duration from frames: {duration:.1f}s.")
                return duration
        except Exception as e:
            print(f"Warning: frame-count fallback failed for '{os.path.basename(file_path)}': {e}")

    print(f"Warning: tag.duration missing or too small for '{os.path.basename(file_path)}', "
          f"defaulting to {DEFAULT_FALLBACK_DURATION}s ({DEFAULT_FALLBACK_DURATION//60} min).")
    return DEFAULT_FALLBACK_DURATION


def _get_flac_duration_from_frames(file_path):
    """
    Calculates FLAC duration by counting audio frame block sizes.
    Used when the STREAMINFO header has total_samples = 0 (common in
    streamed/interrupted recordings where the header was never finalized).
    """
    import struct
    with open(file_path, 'rb') as f:
        data = f.read()

    if data[:4] != b'fLaC':
        return None

    # Parse STREAMINFO to get sample_rate
    pos = 4
    sample_rate = None
    while pos < len(data) - 4:
        byte0 = data[pos]
        last_block = (byte0 & 0x80) != 0
        block_type = byte0 & 0x7F
        block_len = struct.unpack('>I', b'\x00' + data[pos+1:pos+4])[0]

        if block_type == 0:  # STREAMINFO
            si = data[pos+4:pos+4+block_len]
            val = struct.unpack('>Q', si[10:18])[0]
            sample_rate = (val >> 44) & 0xFFFFF
            break

        pos += 4 + block_len
        if last_block:
            break

    if not sample_rate:
        return None

    # Skip all metadata blocks to find start of audio frames
    pos = 4
    while pos < len(data) - 4:
        byte0 = data[pos]
        last_block = (byte0 & 0x80) != 0
        block_len = struct.unpack('>I', b'\x00' + data[pos+1:pos+4])[0]
        pos += 4 + block_len
        if last_block:
            break

    # Count total samples by scanning frame headers
    total_samples = 0
    fp = pos
    while fp < len(data) - 4:
        if data[fp] == 0xFF and (data[fp+1] & 0xFE) == 0xF8:
            bs_code = (data[fp+2] >> 4) & 0xF
            if   bs_code == 0x1: block_size = 192
            elif bs_code == 0x2: block_size = 576
            elif bs_code == 0x3: block_size = 1152
            elif bs_code == 0x4: block_size = 2304
            elif bs_code == 0x5: block_size = 4608
            elif 0x8 <= bs_code <= 0xF: block_size = 256 * (1 << (bs_code - 8))
            else: block_size = 4096
            total_samples += block_size
        fp += 1

    return total_samples / sample_rate if total_samples else None

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