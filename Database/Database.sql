CREATE DATABASE IF NOT EXISTS weather_Db;
USE weather_Db;

-- Audio table
CREATE TABLE audiorecording (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `date` DATE,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    file_path TEXT NOT NULL
);

-- weather_data table
CREATE TABLE weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `date` DATE,
    timestamp DATETIME NOT NULL,
    in_temperature DOUBLE,
    out_temperature DOUBLE,
    in_humidity DOUBLE,
    out_humidity DOUBLE,
    wind_speed DOUBLE,
    wind_direction TEXT,
    daily_rain DOUBLE,
    rain_rate DOUBLE
);

-- sensors table (humidity + temperature)
CREATE TABLE sensors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `date` DATE,
    timestamp DATETIME NOT NULL,
    temperature DOUBLE,
    humidity DOUBLE,
    quality TEXT
);

-- Linking tables for relationships between Audio, Weather, and sensors
CREATE TABLE audioenv_link (
    audio_id INT,
    weather_id INT,
    sensors_id INT,
    Foreign Key (Audio_id) REFERENCES audiorecording(id),
    Foreign Key (weather_id) REFERENCES weather_data(id),
    Foreign Key (sensors_id) REFERENCES sensors(id)
);

-- Sample data
INSERT INTO audiorecording (`date`, start_time, end_time, file_path)
VALUES
('2023-10-01', '2023-10-01 12:00:00', '2023-10-01 12:05:00', '/recordings/audio2.wav'),
('2023-10-01', '2023-10-01 13:00:00', '2023-10-01 13:05:00', '/recordings/audio2.wav'),
('2023-10-01', '2023-10-01 14:00:00', '2023-10-01 14:05:00', '/recordings/audio3.wav');

INSERT INTO weather_data (`date`, timestamp, in_temperature, out_temperature, in_humidity, out_humidity, wind_speed, wind_direction, daily_rain, rain_rate)
VALUES
('2023-10-01', '2023-10-01 12:00:00', 22.5, 25.5, 45.0, 50.0, 5.0, 'N', 0.0, 0.0),
('2023-10-01', '2023-10-01 13:00:00', 23.0, 26.0, 44.0, 48.0, 6.0, 'NE', 0.1, 0.2),
('2023-10-01', '2023-10-01 14:00:00', 24.0, 27.5, 43.0, 47.0, 7.0, 'E', 0.3, 0.4);

INSERT INTO sensors (`date`, timestamp, temperature, humidity, quality)
VALUES
('2023-10-01', '2023-10-01 12:00:00', 25.5, 60.0, 'Good'),
('2023-10-01', '2023-10-01 13:00:00', 26.0, 58.0, 'Moderate'),
('2023-10-01', '2023-10-01 14:00:00', 27.5, 55.0, 'Good');

INSERT INTO audioenv_link (audio_id, weather_id, sensors_id)
VALUES (1, 1, 1);