import os

# --- DATABASE CONFIG ---
# Inside Docker, 'host' must match the service name in docker-compose.yml
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'), 
    'user': 'root',
    'password': '040813', # Match this to your MYSQL_ROOT_PASSWORD
    'database': 'WEATHER_DB'
}

# --- FOLDER PATHS ---
# os.path.dirname(os.path.abspath(__file__)) points to the 'Backend' folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask looks for these inside the same folder as app.py
TEMPLATE_FOLDER_PATH = os.path.join(BASE_DIR, 'templates')
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')

# Storage for uploads inside the container
AUDIO_DIRECTORY = os.path.join(BASE_DIR, 'audio_files')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

# Create directories if they don't exist
for d in [AUDIO_DIRECTORY, UPLOAD_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)