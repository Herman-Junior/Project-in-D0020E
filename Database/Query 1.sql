Create DATABASE Weather_Db;
Use Weather_Db;

Create TABLE SENSORS
(
Date CHAR(10),
TID CHAR(10),
LUFTTEMPERATUR Double,					
KVALITE Text
);
Select * From SENSORS;

INSERT INTO SENSORS(Date, TID, LUFTTEMPERATUR, KVALITE) VALUES
('2024-01-01', '12:00', 5.5, 'Good'),
('2024-01-01', '13:00', 6.0, 'Good'),
('2024-01-01', '14:00', 7.2, 'Moderate'),
('2024-01-02', '12:00', 4.8, 'Good'),
('2024-01-02', '13:00', 5.1, 'Good'),
('2024-01-02', '14:00', 6.3, 'Moderate');