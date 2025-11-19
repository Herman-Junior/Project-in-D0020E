CREATE DATABASE Weather_Db; --Creating a database for weather sensor data
Use Weather_Db; --Using the created database

Create TABLE AUDIO_Recording
(
id int AUTO_INCREMENT PRIMARY KEY,
Starttime CHAR(10),
Endtime CHAR(10),
Filepath Text
);

CREATE TABLE Weather_station(
id int AUTO_INCREMENT PRIMARY KEY,
Temperature Double,
Wind_Speed Double,
rainfall Double,
TIMESTAMP CHAR(20)
);

CREATE TABLE SENSORS(      --Tables that store sensor data with acitivity id's
id int AUTO_INCREMENT PRIMARY KEY,
sensor_Date DATE,
sensor_Time TIME,
Temperature Double,					
Quality Text,
Humidity Double
);

-- Inserting sample data into AUDIO_Recording table
INSERT INTO SENSORS(id, Date, Time, Temperature, Humidity, Quality) VALUES
(1, '2023-10-01', '12:00', 25.5, 60.0, 'Good'),
(2, '2023-10-01', '13:00', 26.0, 58.0, 'Moderate'),
(3, '2023-10-01', '14:00', 27.5, 55.0, 'Good');


-- Table Audio_recording operations
SELECT * FROM Audio_Recording; --Query to select all data from audio recording table
DROP TABLE AUDIO_Recording;

-- Table Weather_station operations
SELECT * FROM Weather_station; --Query to select all data from weather station table
DROP TABLE Weather_station;

-- Table SENSORS operations
Select * From SENSORS; --Query to select all data from sensors table
DROP TABLE SENSORS; --Dropping the sensors table

-- Dropping the database
DROP DATABASE Weather_Db;
