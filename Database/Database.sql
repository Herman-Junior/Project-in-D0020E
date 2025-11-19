CREATE DATABASE IF NOT EXISTS Weather_Db;
USE Weather_Db;

-- Audio table
CREATE TABLE AudioRecording (
    id INT AUTO_INCREMENT PRIMARY KEY,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    file_path TEXT NOT NULL
);

-- Weather station table
CREATE TABLE WeatherStation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    temperature DOUBLE,
    wind_speed DOUBLE,
    rainfall DOUBLE
);

-- Sensor table (humidity + temperature)
CREATE TABLE Sensors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    temperature DOUBLE,
    humidity DOUBLE,
    quality TEXT
);

-- Sample data
INSERT INTO Sensors (timestamp, temperature, humidity, quality)
VALUES
('2023-10-01 12:00:00', 25.5, 60.0, 'Good'),
('2023-10-01 13:00:00', 26.0, 58.0, 'Moderate'),
('2023-10-01 14:00:00', 27.5, 55.0, 'Good');


