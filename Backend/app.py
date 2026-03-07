# backend/app.py

from flask import Flask
import os
from config import *
# Import the route handlers (index, get_sensor_api, and get_weather_api)
from routes import(filter_trash_api, get_audio_api, index, get_sensor_api, get_weather_api, get_combined_api, 
                   upload_csv_file, upload_audio_metadata, insert_page, query_page, 
                   audio_page, trash_page, get_audio_environmental_api, audio_details_page, batch_delete_api, restore_api, check_audio_overlap_api,upload_audio_api  )

app = Flask(__name__, 
            template_folder=TEMPLATE_FOLDER_PATH,
            static_folder=STATIC_FOLDER_PATH)

# --- FIX: Add the route for the root path ('/') ---
app.add_url_rule('/', 'index', index)
app.add_url_rule('/insert', 'insert_page', insert_page)
app.add_url_rule('/query', 'query_page', query_page)
app.add_url_rule('/audio', 'audio_page', audio_page)
app.add_url_rule('/audio/details', 'audio_details_page', audio_details_page)
app.add_url_rule('/trash', 'trash_page', trash_page)
app.add_url_rule('/api/v1/trash/filter', view_func=filter_trash_api, methods=['GET'])

# Register the distinct API endpoints
app.add_url_rule('/api/v1/sensors', 'get_sensor_api', get_sensor_api)
app.add_url_rule('/api/v1/weather', 'get_weather_api', get_weather_api) 
app.add_url_rule('/api/v1/combined', 'get_combined_api', get_combined_api) #--- new ---
app.add_url_rule('/api/v1/upload', 'upload_csv_file', upload_csv_file, methods=['POST'])
app.add_url_rule('/api/v1/audio', 'get_audio_api', get_audio_api)
app.add_url_rule('/api/v1/audio/upload', 'upload_audio_metadata', 
                upload_audio_metadata, methods=['POST'])
app.add_url_rule('/api/v1/audio/environmental', 'get_audio_with_environmental_api', 
                get_audio_environmental_api)
app.add_url_rule('/api/v1/audio', 'upload_audio_api', upload_audio_api, methods=['POST'])

# NEW: pre-upload overlap check — JS sends the filename here before uploading the file
app.add_url_rule('/api/v1/audio/check-overlap', 'check_audio_overlap_api', check_audio_overlap_api, methods=['POST'])

app.add_url_rule('/api/v1/delete', 'batch_delete_api', batch_delete_api, methods=['POST'])
app.add_url_rule('/api/v1/restore', 'restore_api', restore_api, methods=['POST'])

app.add_url_rule('/api/v1/export', 'export_csv_api', export_csv_api)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)