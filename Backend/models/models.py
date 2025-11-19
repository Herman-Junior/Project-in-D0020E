from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AudioRecording(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  file_path = db.Column(db.String(255), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  end_time = db.Column(db.DateTime, nullable=False)

class WeatherData(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  temperature = db.Column(db.Float, nullable=False)
  humidity = db.Column(db.Float, nullable=False)
  timestamp = db.Column(db.DateTime, nullable=False)  

