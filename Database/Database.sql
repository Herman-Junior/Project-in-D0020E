-- Active: 1764679672854@@127.0.0.1@3306@mysql
-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS weather_Db;

USE weather_Db;

-- 2. Drop tables in reverse order to clear previous incorrect schema (if they exist)
DROP TABLE IF EXISTS audioenv_link;

DROP TABLE IF EXISTS audiorecording;

DROP TABLE IF EXISTS WEATHER_DATA;

DROP TABLE IF EXISTS SENSOR_DATA;

CREATE DATABASE IF NOT EXISTS weather_Db;

USE weather_Db;

-- Audio table
CREATE TABLE audiorecording (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    file_path TEXT NOT NULL
);

-- Weather table
CREATE TABLE WEATHER_DATA (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    date DATE,
    time TIME,
    in_temperature DOUBLE,
    out_temperature DOUBLE,
    in_humidity INT,
    out_humidity INT,
    wind_speed DOUBLE,
    wind_direction VARCHAR(10), -- e.g., 'N', 'SW'
    daily_rain DOUBLE,
    rain_rate DOUBLE
);

-- sensors table (humidity + temperature)
CREATE TABLE SENSOR_DATA (
    sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    date DATE,
    time TIME,
    moisture DOUBLE
);

-- Linking tables for relationships between Audio, Weather, and sensors
CREATE TABLE audioenv_link (
    audio_id INT,
    weather_id INT,
    sensors_id INT,
    Foreign Key (Audio_id) REFERENCES audiorecording (id),
    Foreign Key (weather_id) REFERENCES weather_data (id),
    Foreign Key (sensors_id) REFERENCES sensors (id)
);

