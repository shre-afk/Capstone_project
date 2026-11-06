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
 
1. Install MySQL 8.4 and run `schema.sql` once (`SOURCE path/to/schema.sql;`).
2. `pip install -r requirements.txt`
3. In PowerShell: `$env:MYSQL_PASSWORD = "your-password"`
4. `python run.py` and open http://127.0.0.1:5000
 
No MySQL at hand? `$env:USE_MEMORY_DB = "1"` runs the same app on built-in sample data.



## Hometask 4 · Error handling and tests
 
**Error handling.** `errors.py` holds the error classes of Subsystem 2:
 
| Class                      | HTTP | When                                                  |
|----------------------------|------|-------------------------------------------------------|
| `DataSubsystemError`       | 500  | parent of all of them                                 |
| `ValidationError`          | 400  | bad/missing data, impossible kWh, period backwards    |
| `NotFoundError`            | 404  | building or meter id doesn't exist                    |
| `DuplicateReadingError`    | 409  | that meter already has a value for that time          |
| `DatabaseUnavailableError` | 503  | MySQL is down or unreachable                          |
 
`DataErrorHandler` plugs into Flask and turns any of them into a clean JSON answer.
The plausibility limits (home 5, business 100, public 50 kWh per 15 min) are the
same as in the capstone's `config.toml`.
 
**Tests.** 15 pytest tests in `tests/` (3 for the error classes, 5 for input
validation, 7 for the API through Flask's test client). They use an in-memory
repository, so they run without MySQL:
 
```
python -m pytest -v
```
 
Result: `15 passed`