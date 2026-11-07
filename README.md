# AI-Powered Smart Energy Management System for German Properties

An academic capstone project focused on energy monitoring, consumption analysis, forecasting, and AI-assisted energy optimization for German properties.

## Hometask 2 · Real-Time Data Processing

Joywin's self-contained individual solution is in `hometask_assignments/hometask2/subsystem3_ai_stream/`. Ourvish's separate implementation is in `subsystem2_stream/`. See the [assignment README](hometask_assignments/hometask2/readme.md).

### Team overview

| Member | Matriculation number | Assigned subsystem |
|---|---|---|
| Shreya Patil | 7226047 | Energy Dashboard & Reporting |
| Ourvish Lofur | 7226994 | Data Management & Energy Analytics |
| Joywin Bennis | 7225872 | AI Analyzer & Integration |

### OOP requirements and class diagram

| Requirement | Ourvish's implementation (`subsystem2_stream`) | Joywin's implementation (`subsystem3_ai_stream`) |
|---|---|---|
| Abstract base class | `StreamProcessor(ABC)` declares `process()` with `@abstractmethod` | `StreamProcessor(ABC)` declares `process()` with `@abstractmethod` |
| Inheritance and polymorphism | Seven processing steps and `Pipeline` share the `process(reading)` interface | `PowerFilter`, `CarbonTransformer`, and `Pipeline` implement the same `process(reading)` interface |
| Operator overloading | `__or__` / `__add__` join steps into a `Pipeline` | `filter_stage | transform_stage` calls `__or__` to create a pipeline |
| Iterator | `MeterStream` implements `__iter__` and `__next__` | `MeterStream` explicitly implements `__iter__` and `__next__` |
| Generators | `replay_feed()` yields real OPSD readings; `run()` yields the survivors | `sample_readings()` yields events and `run()` yields accepted results lazily |

Subsystem 3 (Joywin):

```mermaid
classDiagram
    class StreamProcessor {
        <<abstract>>
        +process(reading)*
        +__or__(other) Pipeline
        +run(stream) generator
    }
    class Pipeline {
        +steps
        +process(reading)
    }
    class PowerFilter {
        +min_power_kw
        +process(reading)
    }
    class CarbonTransformer {
        +process(reading)
    }
    class MeterReading {
        +building
        +power_kw
        +active
    }
    class MeterStream {
        +__iter__()
        +__next__() MeterReading
    }
    StreamProcessor <|-- Pipeline
    StreamProcessor <|-- PowerFilter
    StreamProcessor <|-- CarbonTransformer
    Pipeline o-- StreamProcessor : ordered stages
    MeterStream ..> MeterReading : yields
    PowerFilter ..> MeterReading : filters
```

Subsystem 2 (Ourvish):

```mermaid
classDiagram
    class StreamProcessor {
        <<abstract>>
        +process(reading)*
        +run(stream) generator
        +__or__(other) Pipeline
        +__add__(other) Pipeline
    }
    StreamProcessor <|-- Pipeline
    StreamProcessor <|-- InactiveMeterFilter
    StreamProcessor <|-- IntervalCalculator
    StreamProcessor <|-- PlausibilityFilter
    StreamProcessor <|-- ThresholdFilter
    StreamProcessor <|-- CostCarbonCalculator
    StreamProcessor <|-- AfterHoursFlagger
    StreamProcessor <|-- LoadBalanceTracker
    Pipeline o-- StreamProcessor : ordered steps
    class MeterStream {
        +int count
        +__iter__()
        +__next__() MeterReading
    }
    class MeterReading {
        +column
        +building
        +building_type
        +ts
        +total_kwh
        +kwh
        +power_kw
        +extras
    }
    MeterStream ..> MeterReading : hands out
```

### Run

```bash
python hometask_assignments/hometask2/subsystem2_stream/main.py
python -m hometask_assignments.hometask2.subsystem3_ai_stream.demo
```

Run from the repository root. Subsystem 2 replays 42 real OPSD meter readings, of which 20 pass its filters, and prints energy, cost, CO2 and the after-hours share per building. In Subsystem 3, five simulated meter events produce three accepted energy/carbon results. Inactive and sub-threshold readings are filtered out. The implementation uses only the Python standard library.

### Presentation link

**Video:** [Hometask 2 presentation (Google Drive)](https://drive.google.com/file/d/1wbvWZXmCwvsP2SSD4gAbRbj2i9uNSqo2/view?usp=drive_link)  
All team videos: [Google Drive folder](https://drive.google.com/drive/folders/1eVMkck2AjgFbLdQfN-eUD_lYISwNbn4x?usp=drive_link)

## Project Overview

The project aims to develop a Python-based prototype that helps users understand electricity consumption patterns, explore historical energy data, forecast future demand, and obtain AI-assisted energy-saving recommendations.

The prototype uses historical electricity data and analytical methods. It does not require physical energy meters or live IoT devices.

## Project Objectives

- Analyze historical electricity consumption and energy-system data.
- Present energy-related insights through an interactive dashboard.
- Explore forecasting methods for identifying future consumption patterns.
- Develop an AI-assisted energy advisor for explaining analytical results and suggesting potential optimization strategies.
- Establish a modular and maintainable Python project structure.

## Project Scope

This project is an academic prototype for energy monitoring, forecasting, and AI-based optimization.

The initial scope includes:
- Historical data processing and validation.
- Exploratory energy data analysis.
- Forecasting experiments.
- Interactive reporting and visualization.
- AI-assisted explanations and recommendations.

Physical meter integration, live IoT monitoring, and production deployment are outside the initial scope.

## Project Team

- Shreya Patil
- Joywin Bennis
- Ourvish Lofur

## System Subsystems

### 1. Energy Dashboard & Reporting
**Planned technologies:** Streamlit, Plotly

Responsible for presenting energy trends, analytical results, forecasts, and reporting visualizations.

### 2. Data Management & Energy Analytics
**Planned technologies:** Python, Pandas, PostgreSQL, Scikit-learn, Statsmodels

Responsible for data preparation, validation, exploratory analysis, and supporting forecasting experiments.

### 3. AI Energy Advisor & Integration
**Planned technologies:** LangChain, OpenAI API, Docker

Responsible for AI-assisted interpretation of energy insights and potential energy-saving recommendations.

These are planned subsystem technologies; integration and compatibility will be verified as development progresses.

## Dataset

**Planned initial source:** Open Power System Data (OPSD), using relevant historical German electricity data.

The selected dataset and its columns will be reviewed before analysis begins. National electricity-system data represents broader electricity demand and is not automatically equivalent to an individual property's consumption.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming language | Python |
| Data processing | Pandas, NumPy |
| Visualization | Plotly |
| Dashboard | Streamlit |
| Machine learning | Scikit-learn |
| Statistical forecasting | Statsmodels |
| Configuration | python-dotenv |
| Planned AI integration | LangChain, OpenAI API |
| Planned database | PostgreSQL |
| Planned containerization | Docker |

## Repository Structure


```text
Capstone_project/
|-- .streamlit/
|   `-- config.toml
|-- src/
|   |-- app.py
|   |-- data/
|   |   |-- __init__.py
|   |   `-- loader.py
|   `-- ui/
|       |-- __init__.py
|       `-- dashboard/
|           |-- __init__.py
|           |-- *.py
|           `-- static/
|-- .env.example
|-- .gitignore
|-- pyproject.toml
|-- README.md
`-- requirements.txt
```

Local virtual environments, generated Python files, and downloaded datasets are excluded from version control.

## Development Environment

The project currently uses Python 3.14.7 in a repository-local virtual environment.

The initial data analysis, visualization, dashboard, forecasting, and configuration dependencies have been installed and tested for successful imports. Additional dependencies will be evaluated when their subsystems are developed.

### Initial Setup

1. Clone the repository.
2. Open the project in PyCharm.
3. Create or select a local virtual environment.
4. Install the initial dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Verify dependency consistency:

   ```bash
   python -m pip check
   ```

### Run the Dashboard

From the project directory:

```bash
python -m streamlit run src/app.py
```

### Environment Variables

Copy `.env.example` to `.env` for local configuration when AI integration is introduced.

Add your own API credentials to `.env` only when needed. Never commit `.env` or expose API keys in source code.

## Visual Theme

The planned dashboard theme is **Midnight Blue + Sand + Bronze**.

| Color | Hex |
|---|---|
| Midnight Blue | `#1E3045` |
| Slate Blue | `#344B63` |
| Warm Sand | `#F3EADF` |
| Bronze | `#C09262` |
| Espresso Brown | `#49372B` |

The theme is documented here for consistency; dashboard UI implementation will follow once the project is ready for that stage.

## Project Status

**Current phase:** Repository setup and environment validation.

Completed:
- Initial repository structure.
- Python package initialization files.
- Git ignore rules and environment template.
- Initial dependency installation and import checks.
- Local interpreter configuration in PyCharm.

Next planned steps include project metadata, dataset assessment, data processing design, and subsystem development.

## Academic Use

This project is intended for educational and demonstration purposes. Forecasts and AI-generated recommendations should be evaluated against the available data and should not be treated as guaranteed energy savings.
