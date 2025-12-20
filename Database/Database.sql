-- 1. Completely remove the database if it exists
-- This deletes all tables, data, and constraints in one go.
DROP DATABASE IF EXISTS WEATHER_DB;

-- 2. Re-create the database
CREATE DATABASE WEATHER_DB;
USE WEATHER_DB;

-- 3. Re-create the tables in the correct order
-- (Parent tables must be created before Child tables that reference them)

CREATE TABLE AUDIO_RECORDING (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    file_path TEXT NOT NULL
);

CREATE TABLE WEATHER_DATA (
    weather_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    date DATE,
    time TIME,
    in_temperature DOUBLE,
    out_temperature DOUBLE,
    in_humidity INT,
    out_humidity INT,
    wind_speed DOUBLE,
    wind_direction VARCHAR(10),
    daily_rain DOUBLE,
    rain_rate DOUBLE
);

CREATE TABLE SENSOR_DATA (
    sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    date DATE,
    time TIME,
    moisture DOUBLE
);

-- This table has Foreign Keys, so it must be created LAST
CREATE TABLE ALL_DATA (
    all_data_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    -- Changed to NULL to allow sensor data to be inserted without weather data
    weather_data_id INT NULL, 
    CONSTRAINT fk_weather
        FOREIGN KEY (weather_data_id)
        REFERENCES WEATHER_DATA(weather_id),
    -- Changed to NULL to allow weather data to be inserted without sensor data
    sensor_data_id INT NULL,
    CONSTRAINT fk_sensor
        FOREIGN KEY (sensor_data_id)
        REFERENCES SENSOR_DATA(sensor_id)
);
