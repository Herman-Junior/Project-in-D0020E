# backend/app.py

from flask import Flask
import os
# Import the route handlers 
from routes import index, get_sensor_api, get_weather_api, upload_csv_file, insert_audio_batch_api, upload_audio_file, get_audio_api

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

FRONTEND_PATH = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_PATH = os.path.join(FRONTEND_PATH, 'static')

app = Flask(__name__, 
            template_folder=FRONTEND_PATH,
            static_folder=STATIC_PATH)

# --- FIX: Add the route for the root path ('/') ---
app.add_url_rule('/', 'index', index)
# ----------------------------------------------------

# Register the distinct API endpoints
app.add_url_rule('/api/v1/sensors', 'get_sensor_api', get_sensor_api)
app.add_url_rule('/api/v1/weather', 'get_weather_api', get_weather_api) 
app.add_url_rule('/api/v1/upload/csv', 'upload_csv_file', upload_csv_file, methods=['POST']) 
# RENAME THE CSV UPLOAD ROUTE for clarity (optional, but recommended)

# NEW AUDIO UPLOAD ROUTE
app.add_url_rule('/api/v1/audio/upload', 'upload_audio_file', upload_audio_file, methods=['POST'])

# Existing Audio Batch Insertion Route
app.add_url_rule('/api/v1/audio/insert', 'insert_audio_batch_api', insert_audio_batch_api, methods=['POST'])

#Audio retrival
app.add_url_rule('/api/v1/audio', 'get_audio_api', get_audio_api)

if __name__ == '__main__':
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)