# Subsystem 3 · Exception handling and automated tests

An independent advisor application with a subsystem error handler, summary validation, and 15 automated tests. Team identification is in the [main README](../../../README.md).

## Install and run the tests

From the repository root, using Python 3.14 or later:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r hometask_assignments/hometask4/subsystem3_advisor/requirements.txt
python -m pytest hometask_assignments/hometask4/subsystem3_advisor/tests -q
```

On Windows, create the environment with `python -m venv .venv` and activate `.venv\Scripts\Activate.ps1`.

Result: **15 passed**. Tests use fresh local summary fixtures and mocked MySQL connections; no running database or model credentials are needed for this suite.

## Error handling

| Exception | HTTP status | Meaning |
|---|---:|---|
| `AdvisorError` | 500 | Base advisor-subsystem exception |
| `SummaryNotFoundError` | 404 | Building summary does not exist |
| `InvalidSummaryError` | 422 | Missing, invalid, or inconsistent summary metrics |
| `AdvisorDatabaseError` | 503 | MySQL connection or query failed |

`AdvisorErrorHandler` registers these exceptions with Flask and returns JSON errors. Unknown URLs and unsupported methods retain 404/405 statuses. Unexpected failures return a safe 500 response. Database errors retain their original cause for server-side diagnosis; responses hide internal database details. Connections are closed in `finally`.

`advisor.py` checks energy, cost, emissions, and after-hours values before generating advice. Values must be numeric, finite, and nonnegative; after-hours consumption cannot exceed total energy.

## Fifteen different tests

| # | Behavior checked |
|---|---|
| 1 | HTML page displays stored energy summaries and advice links |
| 2 | Summary endpoint returns the correct stored JSON values |
| 3 | After-hours consumption produces equipment-schedule advice |
| 4 | Zero after-hours use produces comparison advice |
| 5 | Missing building returns a structured 404 |
| 6 | Unknown URL returns JSON with status 404 |
| 7 | Unsupported HTTP method returns JSON with status 405 |
| 8 | MySQL connection failure becomes a safe 503 |
| 9 | Unexpected failure becomes a safe 500 |
| 10 | Negative, nonnumeric, and boolean energy values are rejected |
| 11 | NaN/infinite emissions are rejected |
| 12 | After-hours energy above the total is rejected |
| 13 | A missing required summary metric is rejected |
| 14 | Building ID is passed as a SQL parameter; dates serialize correctly and the connection closes |
| 15 | A query failure preserves the underlying cause and closes the connection |

The tests are in `tests/test_advisor.py` (13 Flask component tests) and `tests/test_repository.py` (two repository unit tests).

## Run the application with MySQL

The application runs independently of the test fixtures. Install the dependencies above, then configure MySQL and the local credentials:

Install and start MySQL 8.4. Open the MySQL client as an administrator:

```bash
mysql -u root -p
```

Run these commands inside that client, replacing the schema path with its actual absolute path and choosing your own local password:

```sql
SOURCE /absolute/path/to/Capstone_project/hometask_assignments/hometask4/subsystem3_advisor/schema.sql;
CREATE USER IF NOT EXISTS 'advisor_app'@'127.0.0.1' IDENTIFIED BY 'your-local-password';
GRANT SELECT ON energy_advisor.* TO 'advisor_app'@'127.0.0.1';
```

`schema.sql` creates a separate `energy_advisor` database and two synthetic summaries. Running it again preserves existing records. If `advisor_app` already exists, use that account's existing password or choose a new account name and configure it below.

Copy the local configuration template:

```bash
cp hometask_assignments/hometask4/subsystem3_advisor/.env.example hometask_assignments/hometask4/subsystem3_advisor/.env
```

On Windows use `Copy-Item` instead of `cp`. Edit the new `.env` file to set `ADVISOR_DB_PASSWORD` to the password chosen above. Adjust the host, port, user, or database only if your MySQL setup differs. The default port is 3306. Keep the actual `.env` file out of Git.

Start the application:

```bash
python -m hometask_assignments.hometask4.subsystem3_advisor.run
```

Open **http://127.0.0.1:5002/**. MySQL must remain running while the web app is used.

## Web output

- `/`: HTML table of stored summaries.
- `/api/summaries`: stored summaries as JSON.
- `/api/advice/<building_id>`: validated summary and simple rule-based advice.

The seeded office has **192 kWh**, **57.60 EUR**, **72.96 kg CO2**, and **48 kWh after-hours use**. Sample data and factors are demonstration assumptions. Live model integration is outside this implementation.
