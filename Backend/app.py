# backend/app.py

from flask import Flask
import os
# Import the route handlers (index, get_sensor_api, and get_weather_api)
from routes import index, get_sensor_api, get_weather_api, get_combined_api, upload_csv_file, upload_audio_metadata, get_audio_with_environmental_data, insert_page, query_page, audio_page

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

TEMPLATE_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'frontend', 'static')

app = Flask(__name__, 
            template_folder=TEMPLATE_FOLDER_PATH,
            static_folder=STATIC_FOLDER_PATH)

# --- FIX: Add the route for the root path ('/') ---
app.add_url_rule('/', 'index', index)
app.add_url_rule('/insert', 'insert_page', insert_page)
app.add_url_rule('/query', 'query_page', query_page)
app.add_url_rule('/audio', 'audio_page', audio_page)

# Register the distinct API endpoints
app.add_url_rule('/api/v1/sensors', 'get_sensor_api', get_sensor_api)
app.add_url_rule('/api/v1/weather', 'get_weather_api', get_weather_api) 
<<<<<<< HEAD
app.add_url_rule('/api/v1/upload/csv', 'upload_csv_file', upload_csv_file, methods=['POST']) 
# RENAME THE CSV UPLOAD ROUTE for clarity (optional, but recommended)

# NEW AUDIO UPLOAD ROUTE
app.add_url_rule('/api/v1/audio/upload', 'upload_audio_file', upload_audio_file, methods=['POST'])

# Existing Audio Batch Insertion Route
app.add_url_rule('/api/v1/audio/insert', 'insert_audio_batch_api', insert_audio_batch_api, methods=['POST'])

#Audio retrival
app.add_url_rule('/api/v1/audio', 'get_audio_api', get_audio_api)
=======
app.add_url_rule('/api/v1/combined', 'get_combined_api', get_combined_api) #--- new ---
app.add_url_rule('/api/v1/upload', 'upload_csv_file', upload_csv_file, methods=['POST'])
app.add_url_rule('/api/v1/audio/upload', 'upload_audio_metadata', 
                upload_audio_metadata, methods=['POST'])
app.add_url_rule('/api/v1/audio/environmental', 'get_audio_with_environmental_data', 
                get_audio_with_environmental_data)
>>>>>>> origin/main

if __name__ == '__main__':
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)