#backend/app.py

from flask import Flask
import os
# Import the route handlers (index, get_sensor_api, and get_weather_api)
from routes import index, get_sensor_api, get_weather_api, get_combined_api, upload_csv_file, upload_audio_metadata, get_audio_with_environmental_data, insert_page, query_page

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

TEMPLATE_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'frontend', 'static')

app = Flask(__name__, 
            template_folder=TEMPLATE_FOLDER_PATH,
            static_folder=STATIC_FOLDER_PATH)


# Register the routes with the application
# The root URL serves the static HTML file
app.add_url_rule('/', 'index', index)
app.add_url_rule('/insert', 'insert_page', insert_page)
app.add_url_rule('/query', 'query_page', query_page)

# Register the distinct API endpoints
# Note: using the v1 prefix in the URL for versioning (e.g., /api/v1/sensors)
app.add_url_rule('/api/v1/sensors', 'get_sensor_api', get_sensor_api)
app.add_url_rule('/api/v1/weather', 'get_weather_api', get_weather_api) 
app.add_url_rule('/api/v1/combined', 'get_combined_api', get_combined_api) #--- new ---
app.add_url_rule('/api/v1/upload', 'upload_csv_file', upload_csv_file, methods=['POST'])
app.add_url_rule('/api/v1/audio/upload', 'upload_audio_metadata', 
                upload_audio_metadata, methods=['POST'])
app.add_url_rule('/api/v1/audio/environmental', 'get_audio_with_environmental_data', 
                get_audio_with_environmental_data)

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)