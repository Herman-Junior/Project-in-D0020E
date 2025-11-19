CREATE DATABASE IF NOT EXISTS Weather_Db;
USE Weather_Db;

-- Audio table
CREATE TABLE AudioRecording (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `date` DATE,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    file_path TEXT NOT NULL
);

-- Weather station table
CREATE TABLE WeatherDATA (
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

-- Sensor table (humidity + temperature)
CREATE TABLE Sensors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `date` DATE,
    timestamp DATETIME NOT NULL,
    temperature DOUBLE,
    humidity DOUBLE,
    quality TEXT
);


-- Sample data
INSERT INTO AudioRecording (`date`, start_time, end_time, file_path)
VALUES
('2023-10-01', '2023-10-01 12:00:00', '2023-10-01 12:05:00', 'C:\\Users\\Simon Tesfai\\Music\\PioneerDJ\\Sampler\\MERGE FX.wav'),
('2023-10-01', '2023-10-01 13:00:00', '2023-10-01 13:05:00', '/recordings/audio2.wav'),
('2023-10-01', '2023-10-01 14:00:00', '2023-10-01 14:05:00', '/recordings/audio3.wav');

INSERT INTO WeatherDATA (`date`, timestamp, in_temperature, out_temperature, in_humidity, out_humidity, wind_speed, wind_direction, daily_rain, rain_rate)
VALUES
('2023-10-01', '2023-10-01 12:00:00', 22.5, 25.5, 45.0, 50.0, 5.0, 'N', 0.0, 0.0),
('2023-10-01', '2023-10-01 13:00:00', 23.0, 26.0, 44.0, 48.0, 6.0, 'NE', 0.1, 0.2),
('2023-10-01', '2023-10-01 14:00:00', 24.0, 27.5, 43.0, 47.0, 7.0, 'E', 0.3, 0.4);

INSERT INTO Sensors (`date`, timestamp, temperature, humidity, quality)
VALUES
('2023-10-01', '2023-10-01 12:00:00', 25.5, 60.0, 'Good'),
('2023-10-01', '2023-10-01 13:00:00', 26.0, 58.0, 'Moderate'),
('2023-10-01', '2023-10-01 14:00:00', 27.5, 55.0, 'Good');
