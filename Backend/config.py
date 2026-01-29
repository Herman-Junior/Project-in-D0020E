import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '040813',
    'database': 'WEATHER_DB'
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

TEMPLATE_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'frontend', 'static')

AUDIO_DIRECTORY = os.path.join(os.path.dirname(__file__), 'audio_files')
UPLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

if not os.path.exists(AUDIO_DIRECTORY):
    os.makedirs(AUDIO_DIRECTORY)