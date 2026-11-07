# AI-Powered Smart Energy Management System for German Properties

An academic capstone project focused on energy monitoring, consumption analysis, forecasting, and AI-assisted energy optimization for German properties.

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

## Team Overview

| Member | Matriculation number | Assigned subsystem |
|---|---:|---|
| Shreya Patil | 7226047 | 1 · Energy Dashboard & Reporting |
| Ourvish Lofur | 7226994 | 2 · Data Management & Energy Analytics |
| Joywin Bennis | 7225872 | 3 · AI Analyzer & Integration |

### Dashboard OOP implementation

The dashboard subsystem uses three UI classes in `src/ui/dashboard/components.py`:

| Class | Responsibility |
|---|---|
| `DashboardHeader` | Stores and renders a page title and subtitle. |
| `MetricCard` | Validates and renders a styled dashboard metric. |
| `PropertyCard` | Validates and renders a building card with a details action. |

Each class initializes state in `__init__`, exposes validated properties as getters/setters, and provides an `initialize()` method to render its UI. The Overview and Buildings pages use these classes.

## System Design

This GitHub-rendered UML class diagram describes the implemented dashboard components used by the Overview and Buildings pages:

```mermaid
classDiagram
    class DashboardHeader {
        -title: str
        -subtitle: str
        +DashboardHeader(title, subtitle)
        +title: str
        +subtitle: str
        +initialize()
    }
    class MetricCard {
        -label: str
        -value: object
        -key: str
        -icon: str
        -delta: str
        +MetricCard(label, value, key, icon, delta)
        +label: str
        +value: object
        +key: str
        +icon: str
        +delta: str
        +initialize()
    }
    class PropertyCard {
        -building: dict
        +PropertyCard(building)
        +building: dict
        +initialize() bool
    }
    note for DashboardHeader "Used by Overview.py and Buildings.py"
    note for MetricCard "Used on Overview and Buildings"
    note for PropertyCard "Used on Buildings"
```

The approved capstone UML diagrams for the complete system can be added here when available; this diagram documents the implemented dashboard classes only.

## Team Video Presentation

**Presentation link:** Pending team recording and upload. Add the direct YouTube, Loom, or Google Drive URL here when available.

## System Subsystems

### 1. Energy Dashboard & Reporting
**Implemented technologies:** Streamlit, Plotly

Responsible for presenting energy trends, analytical results, forecasts, and reporting visualizations.

### 2. Data Management & Energy Analytics
**Implemented technologies:** Python, Pandas, SQLite

Responsible for data preparation, validation, exploratory analysis, and supporting forecasting experiments.

### 3. AI Energy Advisor & Integration
**Planned technologies:** LangChain, OpenAI API, Docker

Responsible for AI-assisted interpretation of energy insights and potential energy-saving recommendations.

AI Advisor technologies remain planned; integration and compatibility will be verified as development progresses.

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
| Current database | SQLite |
| Planned containerization | Docker |

## Repository Structure


```text
Capstone_project/
|-- .streamlit/
|   `-- config.toml
|-- src/backend/
|   |-- analysis/
|   |-- db/
|   |-- ingestion/
|   |-- models.py
|   `-- settings.py
|-- src/
|   |-- app.py
|   |-- styles/style.css
|   `-- ui/dashboard/
|       |-- components.py
|       |-- Overview.py
|       |-- Buildings.py
|       `-- *.py
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

The dashboard theme is **Midnight Blue + Sand + Bronze**.

| Color | Hex |
|---|---|
| Midnight Blue | `#1E3045` |
| Slate Blue | `#344B63` |
| Warm Sand | `#F3EADF` |
| Bronze | `#C09262` |
| Espresso Brown | `#49372B` |

The theme is applied across the Streamlit dashboard.

## Project Status

**Current phase:** Streamlit dashboard and SQLite-backed energy analysis prototype.

Completed:
- OPSD data ingestion and validation.
- SQLite persistence and Python analysis service layer.
- Streamlit dashboard pages and reusable UI component classes.
- Dashboard OOP class diagram.

Next planned steps include automated tests, team UML consolidation, and the team presentation.

## Academic Use

This project is intended for educational and demonstration purposes. Forecasts and AI-generated recommendations should be evaluated against the available data and should not be treated as guaranteed energy savings.
