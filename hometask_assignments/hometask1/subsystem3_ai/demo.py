"""Offline OOP demonstration. Run from the repository root:

python -m hometask_assignments.hometask1.subsystem3_ai.demo
"""

import json
from types import SimpleNamespace

from .advisor_settings import AdvisorSettings
from .energy_advisor import EnergyAdvisor
from .energy_data_tool import EnergyDataTool


def sample_reader(building_id, start, end):
    """Small fixture with the same required KPI keys as the data subsystem."""
    if building_id != 1:
        raise ValueError("the offline fixture contains only building 1")
    if (start, end) != ("2016-12-01", "2016-12-02"):
        raise ValueError("the fixture covers 1 December 2016 only")
    return {"energy_kwh": 48.0, "cost_eur": 14.4, "co2_kg": 18.2}


def sample_invoke(messages):
    """Deterministic demo response, not an LLM call or an AI-generated answer."""
    context = json.loads(messages[-1][1].split("\n\nQuestion:", 1)[0].split("\n", 1)[1])
    metrics = context["metrics"]
    facts = (f"Building {context['building_id']}: {metrics['energy_kwh']} kWh; "
             f"EUR {metrics['cost_eur']:.2f}; {metrics['co2_kg']} kg CO2.")
    if "Respond in German." in messages[0][1]:
        return SimpleNamespace(content=f"[Offline-Demo] {facts} Pruefen Sie den Verbrauch ausserhalb der Nutzungszeiten.")
    return SimpleNamespace(content=f"[Offline demo] {facts} Review after-hours use; these totals alone do not establish its cause.")


def main():
    settings = AdvisorSettings(language="en", response_style="concise")
    tool = EnergyDataTool()
    tool.initialize(sample_reader)
    advisor = EnergyAdvisor("Portfolio Energy Advisor", settings, tool)
    advisor.initialize(SimpleNamespace(invoke=sample_invoke))

    print("1. Three collaborating objects:")
    for obj in (settings, tool, advisor):
        print("  ", type(obj).__name__)
    print("\n2. Read analytical results and explain them:")
    print(advisor.ask("How can I investigate this building's consumption?", 1,
                      "2016-12-01", "2016-12-02"))

    print("\n3. Change configuration through setters:")
    settings.set_language("de")
    advisor.set_name("Gebaeude-Energieberater")
    print(advisor.get_name(), "language:", advisor.get_settings().get_language())
    print(advisor.ask("Was soll ich untersuchen?", 1, "2016-12-01", "2016-12-02"))

    print("\n4. Encapsulation protects cached data:")
    copy = tool.get_last_result()
    copy["energy_kwh"] = -999
    print("Changing a returned copy leaves stored energy at", tool.get_last_result()["energy_kwh"], "kWh")

    print("\n5. Invalid configuration is rejected:")
    try:
        settings.set_language("invalid")
    except ValueError as error:
        print("setter said no ->", error)


if __name__ == "__main__":
    main()
