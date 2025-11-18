from flask import Flask, render_template, request

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Query route (placeholder for database integration)
@app.route('/query')
def query():
    timestamp = request.args.get('timestamp')
    return f"Query for timestamp: {timestamp}"

if __name__ == '__main__':
    app.run(debug=True)
