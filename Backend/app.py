from flask import Flask, render_template

app = Flask(__name__)

# Define a route for the root URL ('/')
@app.route('/')
def index():
    # Fetch data from the database and prepare for rendering
    data = get_data_from_database()  # Replace this with your actual data retrieval logic
    # Render the 'index.html' template and pass the retrieved data for rendering
    return render_template('index.html', data=data)

# Placeholder for fetching data from the database
def get_data_from_database():
    # Replace this function with your actual logic to retrieve data from the database
    # For now, returning a sample data
    return {'message': 'Hello, data from the database!'}

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)