-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS weather_Db;

USE weather_Db;

-- 2. Drop tables in reverse order to clear previous incorrect schema (if they exist)
DROP TABLE IF EXISTS audioenv_link;

DROP TABLE IF EXISTS audiorecording;

DROP TABLE IF EXISTS weather_data;

DROP TABLE IF EXISTS SENSOR_DATA;

-- 3. Define audiorecording table
CREATE TABLE audiorecording (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `date` DATE,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    file_path TEXT NOT NULL
);

-- 4. Define weather_data table (lowercase, as used in Python query)
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

-- 5. Define SENSOR_DATA table (Uppercase, as used in Python query)
-- CRITICAL FIX: Added sensor_id Primary Key for foreign key linkage
CREATE TABLE SENSOR_DATA (
    sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    `timestamp` DATETIME NOT NULL,
    `date` DATE,
    `time` TIME,
    moisture DOUBLE
);

-- 6. Define Linking table
-- CRITICAL FIX: Foreign Key now correctly points to SENSOR_DATA(sensor_id)
CREATE TABLE audioenv_link (
    audio_id INT,
    weather_id INT,
    sensors_id INT,
    Foreign Key (audio_id) REFERENCES audiorecording (id),
    Foreign Key (weather_id) REFERENCES weather_data (id),
    Foreign Key (sensors_id) REFERENCES SENSOR_DATA (sensor_id)
);

-- Insert audioenv_link data (linking the first record from each table)
INSERT INTO
    audioenv_link (
        audio_id,
        weather_id,
        sensors_id
    )
VALUES (1, 1, 1);