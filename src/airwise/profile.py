"""② User Profile。"""
from dataclasses import dataclass


@dataclass
class Profile:
    group: str = "general"        # general | sensitive | student
    home_town: str | None = None  # 例如 "西屯區"
    lat: float | None = None
    lon: float | None = None
