"""Coordinate advisor settings, analytical data, and a LangChain-style runnable."""

import json

from .advisor_settings import AdvisorSettings
from .energy_data_tool import EnergyDataTool


class EnergyAdvisor:
    def __init__(self, name, settings, data_tool):
        self._chain = None
        self._last_answer = None
        self.set_name(name)
        self.set_settings(settings)
        self.set_data_tool(data_tool)

    def initialize(self, chain):
        """Inject a runnable exposing invoke(messages); no provider is hardcoded."""
        if not callable(getattr(chain, "invoke", None)):
            raise TypeError("the advisor chain must provide invoke(messages)")
        self._chain = chain
        self._last_answer = None

    def ask(self, question, building_id, start, end):
        if self._chain is None:
            raise RuntimeError("initialize the advisor with a runnable first")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("enter a nonempty energy question")
        metrics = self._data_tool.fetch(building_id, start, end)
        context = {"building_id": building_id, "start": str(start), "end": str(end),
                   "metrics": metrics}
        messages = [
            ("system", self._settings.build_system_message()),
            ("human", f"Analytical context:\n{json.dumps(context, default=str, allow_nan=False)}"
             f"\n\nQuestion: {question.strip()}"),
        ]
        response = self._chain.invoke(messages)
        # LangChain chat models return an AIMessage; a string-output chain
        # returns text directly. Both forms can be connected to this class.
        answer = response if isinstance(response, str) else getattr(response, "content", None)
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("the configured runnable must return nonempty text")
        self._last_answer = answer.strip()
        return self._last_answer

    def get_name(self):
        return self._name

    def get_settings(self):
        return self._settings

    def get_data_tool(self):
        return self._data_tool

    def get_last_answer(self):
        return self._last_answer

    def set_name(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("the advisor needs a name")
        self._name = name.strip()

    def set_settings(self, settings):
        if not isinstance(settings, AdvisorSettings):
            raise TypeError("settings must be an AdvisorSettings object")
        self._settings = settings
        self._last_answer = None

    def set_data_tool(self, data_tool):
        if not isinstance(data_tool, EnergyDataTool):
            raise TypeError("data_tool must be an EnergyDataTool object")
        self._data_tool = data_tool
        self._last_answer = None
