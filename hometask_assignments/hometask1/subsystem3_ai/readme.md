# Subsystem 3 · AI Analyzer & Integration

Joywin Bennis · Matriculation number 7225872 · joywin.bennis004@stud.fh-dortmund.de

Part of Hometask 1, Group 30, M1-05 Compact Programming Course (Python), FH Dortmund.

## Classes

- **AdvisorSettings:** private configuration, validated setup, getters, and setters.
- **EnergyDataTool:** initialize a read-only KPI reader; fetch validated energy/cost/emissions; protect cached results using copies.
- **EnergyAdvisor:** initialize a LangChain-compatible runnable; assemble system/user messages from settings and analytical results; retrieve an answer.

Each class has an explicit constructor and setup/configuration methods. Classes collaborate through composition and injected dependencies. The detailed UML appears in the [assignment README](../readme.md).

## Run

From the repository root:

```bash
python -m hometask_assignments.hometask1.subsystem3_ai.demo
```

No additional packages, database, network access, or model credentials are needed for this demonstration. The sample reader and response are deterministic fixtures; live LangChain integration is a separate connection step using `initialize(...)`.
