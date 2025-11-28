# backend/app.py
from flask import Flask
# Import the route handler from the local routes module
from routes import index

app = Flask(__name__)

# Register the routes with the application
# When a user visits '/', the index function from routes.py is executed.
app.add_url_rule('/', 'index', index)

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)