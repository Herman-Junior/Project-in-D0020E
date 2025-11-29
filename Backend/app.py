#backend/app.py

from flask import Flask
# Import the route handlers (index, get_sensor_api, and get_weather_api)
from routes import index, get_sensor_api, get_weather_api, upload_csv_file

app = Flask(__name__)

# Register the routes with the application
# The root URL serves the static HTML file
app.add_url_rule('/', 'index', index)

# Register the distinct API endpoints
# Note: using the v1 prefix in the URL for versioning (e.g., /api/v1/sensors)
app.add_url_rule('/api/v1/sensors', 'get_sensor_api', get_sensor_api)
app.add_url_rule('/api/v1/weather', 'get_weather_api', get_weather_api) 
app.add_url_rule('/api/v1/upload', 'upload_csv_file', upload_csv_file, methods=['POST'])

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)