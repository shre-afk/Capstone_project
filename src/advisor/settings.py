"""Local KI Connect configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AdvisorSettings:
    api_key: str = field(repr=False)
    model: str
    base_url: str = "https://chat.kiconnect.nrw/api/v1"
    timeout: float = 30.0
    max_model_calls: int = 5
    max_tool_calls: int = 8

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env")

        return cls(
            api_key=os.getenv("KICONNECT_API_KEY"),
            model=os.getenv("KICONNECT_MODEL"),
            base_url=os.getenv("KICONNECT_BASE_URL", cls.base_url),
        )