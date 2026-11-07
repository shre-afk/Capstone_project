# Hometask 4 · Exception handling and automated tests

Each implementation has its own error-handling class and test suite. Team identification is in the [main README](../../README.md).

| Subsystem | Handler | Tests | Documentation |
|---|---|---:|---|
| Data Management & Analytics | `DataErrorHandler` | 15 | [Subsystem 2](subsystem2_flask/readme.md) |
| AI Analyzer & Integration | `AdvisorErrorHandler` | 15 | [Subsystem 3](subsystem3_advisor/readme.md) |

## System design

See the [advisor UML class diagram](../../README.md#advisor-uml-class-diagram) in the main README for the exception hierarchy, repository, and error handler.

## Advisor test command

From the repository root, install `subsystem3_advisor/requirements.txt`, then run:

```bash
python -m pytest hometask_assignments/hometask4/subsystem3_advisor/tests -q
```

The advisor suite checks normal web output, advice rules, invalid summaries, missing resources, safe server errors, parameterized SQL, and connection cleanup. It runs without MySQL using local fixtures and mocked connections. Recorded result: **15 passed**.

The two implementations are independent. Their production data and application files are contained in their respective folders.
