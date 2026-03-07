# Project-in-D0020E 2025/2026
Integrating Sensor and Audio Data Using a Relational Database System

---

## Table of Contents

- [Project Goals and Background](#project-goals-and-background)
- [Requirements and Deliverables](#requirements-and-deliverables)
- [Technical Architecture](#technical-architecture)
- [Installation Guide](#installation-guide)
- [Collaborators](#collaborators)

---

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

---

## Technical Architecture

The system is built as a three-tier web application: a browser-based frontend, a Python/Flask backend, and a MySQL relational database.

### Technology Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

### Project Structure

```
Project-in-D0020E/
├── Backend/
│   ├── app.py            # Application entry point, URL registration
│   ├── config.py         # Database credentials and folder paths
│   ├── routes.py         # HTTP endpoint handlers
│   ├── services.py       # Business logic (queries, audio upload, overlap handling)
│   ├── db.py             # Database access layer (all SQL)
│   ├── data_loader.py    # CSV parsing and bulk insertion
│   ├── utils.py          # Shared utilities (timestamps, metadata, filtering)
│   ├── templates/        # Jinja2 HTML templates
│   └── static/scripts/   # Frontend JavaScript
├── Database/             # SQL schema and EER diagram
├── mock_sensor_data.csv  # Example sensor data for testing
├── mock_weather_data.csv # Example weather data for testing
└── README.md
```

---

## Installation Guide

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- `pip` package manager

### 1. Clone the Repository

```bash
git clone https://github.com/Herman-Junior/Project-in-D0020E.git
cd Project-in-D0020E
```

### 2. Create a Virtual Environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r Backend/requirements.txt
```

### 4. Set Up the Database

Open your MySQL client and create a database, then run the schema file found in the `Database/` folder:

```sql
CREATE DATABASE weather_db;
```

### 5. Configure the Application

Open `Backend/config.py` and update the database credentials to match your MySQL setup:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_username',
    'password': 'your_mysql_password',
    'database': 'weather_db'
}
```

### 6. Run the Application

```bash
python -m Backend.app
```

The application will be available at **http://localhost:5000**

### 7. Test with Sample Data

Mock CSV files are included in the project root for testing:

- `mock_sensor_data.csv` — sample moisture/humidity sensor readings
- `mock_weather_data.csv` — sample weather station readings

Navigate to the **Insert** page and upload these files to populate the database.

---

## Collaborators

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/Herman-Junior">
        <img src="https://github.com/Herman-Junior.png" width="80px" alt="Herman"/><br/>
        <sub><b>Herman Ghafouri</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Iwanstahl">
        <img src="https://github.com/Iwanstahl.png" width="80px" alt="Isak"/><br/>
        <sub><b>Isak Wanstål</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/flwrgfriend">
        <img src="https://github.com/flwrgfriend.png" width="80px" alt="Linda"/><br/>
        <sub><b>Linda El-Nagar</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/SimonTesfai">
        <img src="https://github.com/SimonTesfai.png" width="80px" alt="Simon"/><br/>
        <sub><b>Simon Tesfai</b></sub>
      </a>
    </td>
  </tr>
</table>

---

*Luleå University of Technology — D0020E Project in Computer Science and Engineering, LP2–LP3 2025/2026*
