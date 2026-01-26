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
    file_path VARCHAR(255) NOT NULL UNIQUE -- New code: file_path must be UNIQUE so we can 'REPLACE' if the file is re-uploaded
);

-- Weather table
CREATE TABLE WEATHER_DATA (
    weather_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL UNIQUE, -- New: idtenifies a duplicate row.
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
    timestamp DATETIME NOT NULL UNIQUE, -- Uniquie Contraint
    date DATE,
    time TIME,
    moisture DOUBLE
);

CREATE TABLE ALL_DATA (
    all_data_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL UNIQUE, -- -- NEW: UNIQUE here too
    -- Changed to NULL to allow sensor data to be inserted without weather data
    weather_data_id INT NULL, 
    CONSTRAINT fk_weather
        FOREIGN KEY (weather_data_id)
        REFERENCES WEATHER_DATA(weather_id),
        ON DELETE SET NULL, -- -- NEW: Allows replacement without error
    -- Changed to NULL to allow weather data to be inserted without sensor data
    sensor_data_id INT NULL,
    CONSTRAINT fk_sensor
        FOREIGN KEY (sensor_data_id)
        REFERENCES SENSOR_DATA(sensor_id)
        ON DELETE SET NULL
);


SELECT
    A.timestamp,

    W.in_temperature,
    W.out_temperature,
    W.in_humidity,
    W.out_humidity,
    W.wind_speed,
    W.wind_direction,
    W.daily_rain,
    W.rain_rate,

    S.moisture
FROM
    ALL_DATA A
INNER JOIN
    WEATHER_DATA W ON A.weather_data_id = W.weather_id
INNER JOIN
    SENSOR_DATA S ON A.sensor_data_id = S.sensor_id
WHERE
    W.is_deleted = 0 -- Hides weather data marked as deleted
    AND S.is_deleted = 0 -- Hides sensor data marked as deleted
    AND A.timestamp = '2025-12-13 19:00:00'; -- Filter on the timestamp you just inserted


-- Add soft delete flag to Audio recordings
ALTER TABLE AUDIO_RECORDING 
ADD COLUMN is_deleted TINYINT(1) DEFAULT 0;

-- Add soft delete flag to Weather data
ALTER TABLE WEATHER_DATA 
ADD COLUMN is_deleted TINYINT(1) DEFAULT 0;

-- Add soft delete flag to Sensor data
ALTER TABLE SENSOR_DATA 
ADD COLUMN is_deleted TINYINT(1) DEFAULT 0;

-- This creates a shortcut to see all deleted weather entries
CREATE VIEW DELETED_WEATHER AS
SELECT * FROM WEATHER_DATA 
WHERE is_deleted = 1;

CREATE VIEW DELETED_SENSOR AS
SELECT * FROM SENSOR_DATA   
WHERE is_deleted = 1;

CREATE VIEW DELETED_AUDIO AS
SELECT * FROM AUDIO_RECORDING  
WHERE is_deleted = 1;