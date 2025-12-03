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
        format = r'(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})'
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
    

def extract_batch_metadata(audio_directory):

    
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









# test

""" if __name__ == "__main__":
    # Example 1: Process all audio files in a directory
    audio_dir = r"C:\Users\herma\Videos\4K Video Downloader"
    all_metadata = extract_batch_metadata(audio_dir)  # Fixed: was 'audio_directory'
    
    print(f"Found {len(all_metadata)} audio files\n")
    
    # Loop through all audio files found
    for metadata in all_metadata:
        print(f"Filename: {metadata['filename']}")
        print(f"Duration: {metadata['duration']:.2f} seconds")
        print(f"Full path: {metadata['filepath']}")
        print(f"Start timestamp: {metadata['start_timestamp']}")
        print(f"End timestamp: {metadata['end_timestamp']}")
        print("-" * 50)

 """






















""" MIT License

Copyright (c) 2014-2025 Tom Wallroth, Mat (mathiascode), et al.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. """