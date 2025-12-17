import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '031021',
    'database': 'Weather_Db'
}


# where the audiofiles are stored
AUDIO_DIRECTORY = os.path.join(os.path.dirname(__file__), 'audio_files')
UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

if not os.path.exists(AUDIO_DIRECTORY):
    os.makedirs(AUDIO_DIRECTORY)