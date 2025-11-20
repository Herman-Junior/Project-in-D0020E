# Project-in-D0020E 2025/2026
Integrating Sensor and Audio Data Using a Relational Database System
## Project goals and Background
In engineering systems, collecting and managing data from various sensors and devices is fundamental for monitoring performance, detecting patterns, and supporting decision-making. Different types of data, such as environmental measurements, audio recordings, or sensor outputs, are often generated simultaneously but stored separately. Without an efficient way to organize and relate these datasets, valuable insights can be easily lost. This project focuses on designing and implementing a database system capable of storing, organizing, and linking heterogeneous data sources. The data will include audio recordings, measurements from a weather station such as temperature, wind speed, and air pressure, as well as humidity sensor readings.

**The primary goals** are to design the EER diagram of the database, manage different types of data including audio files and sensor data, define and manage relationships between datasets such as linking a specific audio recording to environmental conditions measured at the same time, query and download selected data based on custom filters or time intervals, and document the implementation process, challenges, and insights from the experiments.

For example, a user should be able to retrieve all humidity and weather parameters corresponding to the exact period when a specific audio file was recorded. This will require designing a suitable database schema, developing interfaces for data interaction, and ensuring consistency between related datasets.

## Requirements and Deliverables
The hardware and software requirements for the project include two Raspberry Pi boards and a Vantage PRO 2 weather station. However, the physical hardware setup is not required to be implemented, and the outdoor setup can be ignored. These components represent the real-world environment where data would normally be collected, but for this project, pre-recorded or simulated data provided in CSV format will be used instead.
Each CSV file could contain representative data such as:

humidity, temperature, timestamp...

2.1, 20.5, 1762180897
2.1, 20.5, 1762180898
2.1, 20.5, 1762180899

The **goal** is to extract and import these data into the database system rather than uploading the CSV files themselves.
The software requirements include any communication backend that works, such as Flask, and any reasonable frontend such as Flask combined with HTML and JavaScript.

The project deliverables consist of several components. 
First, the database setup documentation should include a step-by-step guide on how to set up the system, both hardware and software, how data should be collected to be added to the database, and the database EER diagram. 

Second, the database framework and codebase should provide modular scripts for tasks such as upload, download, and query, along with configuration details and instructions for using the system, including searching for a specific date or audio file. 

Third, a benchmarking and analysis report should describe how the system can run on any computer, specify where audio files are stored, and explain that audio files should be referenced by file paths rather than stored directly in the database. It should also address special cases such as missing audio data associated with certain measurements and multiple audio recordings of different durations, including filtering or prioritizing relevant files within a specific duration range.

Additionally, the report should explore how the entire system could be deployed online. Fourth, a demonstration and presentation should be prepared as defined by the D0020E course. Finally, a comprehensive project report should also be delivered according to the course requirements.

# To Run:
- Have flask, MySQL, pymysql packages installed.
- From folder run: python -m backend.app
