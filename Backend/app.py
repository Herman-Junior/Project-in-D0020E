import pymysql
from flask import Flask, render_template

app = Flask(__name__)

# Function to establish and close connection safely
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='031021',
        database='Weather_Db'
    )

# Actual logic to retrieve data from the database
def get_data_from_database():
    conn = None
    data = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor) # Use DictCursor to get results as dictionaries
        
        # Select all columns from the Sensors table
        cursor.execute("SELECT id, timestamp, temperature, humidity, quality FROM Sensors ORDER BY timestamp DESC LIMIT 5")
        
        # Fetch all results
        data = cursor.fetchall()
    
    except Exception as e:
        print(f"Database Error: {e}")
        # Optionally, handle the error more gracefully for the user
        data = [{'error': f"Failed to load data: {e}"}]
        
    finally:
        # Always close the connection
        if conn:
            conn.close()
            
    return data

# Define a route for the root URL ('/')
@app.route('/')
def index():
    # Fetch data from the database
    sensor_data = get_data_from_database()
    
    # Render the 'index.html' template and pass the data
    return render_template('index.html', sensor_data=sensor_data)

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)