# Hometask 3 · Web APIs & Database Access Layers

The assignment uses Flask to display data stored in MySQL. Team identification is in the [main README](../../README.md).

| Folder | Implementation |
|---|---|
| [subsystem2_flask](subsystem2_flask/readme.md) | Data service: buildings, meter readings, and KPIs |
| [subsystem3_advisor](subsystem3_advisor/readme.md) | Energy advisor: stored summaries, HTML output, and JSON advice |

The implementations run separately. Subsystem 3 uses its own database and dependencies; it does not require edits to subsystem 2.

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
