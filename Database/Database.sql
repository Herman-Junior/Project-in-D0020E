-- Active: 1764679672854@@127.0.0.1@3306@mysql
-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS WEATHER_DB;

USE WEATHER_DB;

-- 2. Drop tables in reverse order to clear previous incorrect schema (if they exist)
DROP TABLE IF EXISTS audioenv_link;

DROP TABLE IF EXISTS audio_recording;

DROP TABLE IF EXISTS WEATHER_DATA;

DROP TABLE IF EXISTS SENSOR_DATA;

DROP TABLE IF EXISTS ALL_DATA;

DROP DATABASE IF EXISTS WEATHER_DB;

-- Audio table
CREATE TABLE AUDIO_RECORDING (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    file_path TEXT NOT NULL
);

-- Weather table
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
-- Combined data table
CREATE TABLE ALL_DATA (
    all_data_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,

    
    weather_data_id INT NOT NULL,
    CONSTRAINT fk_weather
        FOREIGN KEY (weather_data_id)
        REFERENCES WEATHER_DATA(weather_id),

    
    sensor_data_id INT NOT NULL,
    CONSTRAINT fk_sensor
        FOREIGN KEY (sensor_data_id)
        REFERENCES SENSOR_DATA(sensor_id)
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
    A.timestamp = '2025-12-13 19:00:00'; -- Filter on the timestamp you just inserted