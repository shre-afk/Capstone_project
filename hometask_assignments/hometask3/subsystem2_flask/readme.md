# Hometask 3 · Flask web API + MySQL (Subsystem 2 data service)

**Author:** Ourvish Lofur · Matr. no. 7226994 · ESE · Group 30  
**Subsystem:** 2 · Data Management & Energy Analytics

A small Flask app on a MySQL copy of our capstone data model
(building -> zone -> meter -> reading, six OPSD buildings). All SQL lives in one
class (`MySQLRepository`); the web part never touches the database directly.
The KPI names match the capstone's `api.get_kpis()`.

## Endpoints

| Method | URL                                          | What you get                         |
|--------|----------------------------------------------|--------------------------------------|
| GET    | `/`                                          | HTML table of all buildings          |
| GET    | `/api/buildings`                             | all buildings as JSON                |
| GET    | `/api/buildings/<id>`                        | one building                         |
| GET    | `/api/buildings/<id>/readings?start=&end=`   | its 15-min values (UTC)              |
| GET    | `/api/buildings/<id>/kpis?start=&end=`       | energy_kwh, cost_eur, co2_kg         |
| POST   | `/api/readings`                              | add one value: meter_id, ts_utc, value |

## How to run

All commands from the repository root, in PowerShell.

1. Install the packages (ideally inside a virtual environment):
   ```
   pip install -r hometask_assignments/hometask3/subsystem2_flask/requirements.txt
   ```
2. Once: create the database user and load the tables and sample data. In the MySQL shell, logged in as root:
   ```sql
   CREATE USER 'energy_app'@'localhost' IDENTIFIED BY 'choose-a-password';
   GRANT ALL PRIVILEGES ON energy_hometask.* TO 'energy_app'@'localhost';
   SOURCE hometask_assignments/hometask3/subsystem2_flask/schema.sql;
   ```
3. Give the app its password. All logins come from environment variables, so no password is stored in the code:
   ```
   $env:MYSQL_PASSWORD = "choose-a-password"
   ```
   Optional, with their defaults: `MYSQL_HOST` (localhost), `MYSQL_PORT` (3306), `MYSQL_USER` (energy_app), `MYSQL_DATABASE` (energy_hometask).
4. Start it and open http://127.0.0.1:5000
   ```
   python hometask_assignments/hometask3/subsystem2_flask/run.py
   ```

No MySQL at hand? `$env:USE_MEMORY_DB = "1"` runs the same app on built-in sample data.
