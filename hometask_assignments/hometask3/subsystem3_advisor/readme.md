# Subsystem 3 · Flask and MySQL energy advisor

A small web application that reads building energy summaries from MySQL, displays them in an HTML table, and returns summaries and advice as JSON. Advice uses a simple after-hours rule; no live model integration or API key is needed.

Team identification and subsystem responsibilities are in the [main README](../../../README.md).

## Setup

Run from the repository root with Python 3.14 or later:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r hometask_assignments/hometask3/subsystem3_advisor/requirements.txt
```

On Windows, create the environment with `python -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1`.

Install and start MySQL 8.4. Open the MySQL client as an administrator:

```bash
mysql -u root -p
```

Run these commands inside that client, replacing the schema path with its actual absolute path and choosing your own local password:

```sql
SOURCE /absolute/path/to/Capstone_project/hometask_assignments/hometask3/subsystem3_advisor/schema.sql;
CREATE USER IF NOT EXISTS 'advisor_app'@'127.0.0.1' IDENTIFIED BY 'your-local-password';
GRANT SELECT ON energy_advisor.* TO 'advisor_app'@'127.0.0.1';
```

`schema.sql` creates a separate `energy_advisor` database and two synthetic summaries. Running it again preserves existing records. If `advisor_app` already exists, use that account's existing password or choose a new account name and configure it below.

Copy the local configuration template:

```bash
cp hometask_assignments/hometask3/subsystem3_advisor/.env.example hometask_assignments/hometask3/subsystem3_advisor/.env
```

On Windows use `Copy-Item` instead of `cp`. Edit the new `.env` file to set `ADVISOR_DB_PASSWORD` to the password chosen above. Adjust the host, port, user, or database only if your MySQL setup differs. The default port is 3306. Keep the actual `.env` file out of Git.

Start the application:

```bash
python -m hometask_assignments.hometask3.subsystem3_advisor.run
```

Open **http://127.0.0.1:5002/**. MySQL must remain running while the web app is used.

## Endpoints

| Method | Route | Output |
|---|---|---|
| GET | `/` | HTML table of MySQL energy summaries |
| GET | `/api/summaries` | All stored summaries as JSON |
| GET | `/api/advice/1` | One building's summary and rule-based advice |

A missing building returns 404. There are no database write endpoints; the web application's database user only needs `SELECT` permission.

```bash
curl http://127.0.0.1:5002/api/summaries
curl http://127.0.0.1:5002/api/advice/2
```

The seeded office has **192 kWh**, **57.60 EUR**, **72.96 kg CO2**, and **48 kWh after-hours use** for 1 December 2016. Its advice suggests reviewing equipment schedules. Data and factors are demonstration assumptions.

## Files

- `app.py`: Flask routes and the advice rule.
- `repository.py`: parameterized MySQL queries and connection cleanup.
- `config.py`: credentials loaded from this folder's `.env` or environment variables.
- `run.py`: starts the app on local port 5002.
- `schema.sql`: table and sample data.
- `templates/index.html`: database output page.

This implementation is independent of subsystem 2 and the capstone's database code.
