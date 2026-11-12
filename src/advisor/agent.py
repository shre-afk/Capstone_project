from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from advisor.model import get_model
from advisor.prompts import SYSTEM_PROMPT
from advisor.tools import (
    list_buildings,
    get_consumption,
    compare_buildings,
)


def get_agent():
    return create_agent(
        model=get_model(),
        tools=[list_buildings, get_consumption, compare_buildings],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
