# Hometask 3 · Web APIs & Database Access Layers

The assignment uses Flask to display data stored in MySQL. Team identification is in the [main README](../../README.md).

| Folder | Implementation |
|---|---|
| [subsystem2_flask](subsystem2_flask/readme.md) | Data service: buildings, meter readings, and KPIs |
| [subsystem3_advisor](subsystem3_advisor/readme.md) | Energy advisor: stored summaries, HTML output, and JSON advice |

The implementations run separately. Subsystem 3 uses its own database and dependencies; it does not require edits to subsystem 2.

## Subsystem 2 requirements

| Requirement | Implementation |
|---|---|
| Flask application | `subsystem2_flask/app.py`, built by `create_app(repository)` (the repository is passed in, so the same app runs on MySQL or on test data) |
| MySQL database access | `MySQLRepository` in `repository.py`: the only class that contains SQL, uses `%s` placeholders against SQL injection, and closes every connection in `finally` |
| Data output | HTML table of the six buildings at `/`; JSON for buildings, 15-minute readings and KPIs (energy, cost, CO2); `POST /api/readings` stores a new value |
| Identification and project README | Main README and the linked setup instructions |

Follow [subsystem 2 setup instructions](subsystem2_flask/readme.md) to install the dependencies, create the database/user, and set the password. Then run from the repository root:

```bash
python hometask_assignments/hometask3/subsystem2_flask/run.py
```

Open http://127.0.0.1:5000/ for the HTML page or `/api/buildings/4/kpis` for JSON output. Without MySQL, set `USE_MEMORY_DB=1` to run the same app on built-in sample data.

## Subsystem 3 requirements

| Requirement | Implementation |
|---|---|
| Flask application | `subsystem3_advisor/app.py` |
| MySQL database access | `EnergyRepository` in `repository.py` |
| Data output | HTML summary table and JSON routes |
| Identification and project README | Main README and the linked setup instructions |

Follow [subsystem 3 setup instructions](subsystem3_advisor/readme.md) to install the dependencies, create the database/user, and configure credentials. Then run from the repository root:

```bash
python -m hometask_assignments.hometask3.subsystem3_advisor.run
```

Open http://127.0.0.1:5002/ for the HTML page or `/api/summaries` for JSON output. Advice is rule-based for this prototype.
