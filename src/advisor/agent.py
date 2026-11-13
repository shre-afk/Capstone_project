from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from advisor.model import get_model
from advisor.prompts import SYSTEM_PROMPT
from advisor.tools import (
    list_buildings,
    get_data_availability,
    get_consumption,
    compare_buildings,
    get_peak_usage,
)


def get_agent():
    return create_agent(
        model=get_model(),
        tools=[list_buildings, get_data_availability, get_consumption, compare_buildings, get_peak_usage],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
