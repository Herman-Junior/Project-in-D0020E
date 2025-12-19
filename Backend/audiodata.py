from tinytag import TinyTag
import os
import re
from datetime import datetime
from config import AUDIO_DIRECTORY

def extract_audio_metadata(file_path):
    try:
        # check if exists
        if not os.path.exists(file_path):
            print(f"File not found - {file_path}")
            return None
        
        # duration
        tag = TinyTag.get(file_path)

        filename = os.path.basename(file_path)

        # timestamp
        timestamp = None
        cleaned_name = os.path.splitext(filename)[0]

        # YYYY_MM_DD_HH_MM_SS format
        format = r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
        match = re.search(format, cleaned_name)

        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))


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
