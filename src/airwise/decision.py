"""⑦ Decision：預防原則與建議合成（對應 Pseudocode 第 15–22 行）。"""
from __future__ import annotations

from dataclasses import dataclass, field

from airwise.rules.engine import RuleEngine, RuleResult


@dataclass
class Forecast:
    aqi: float          # 點預測 ŷ
    lo: float           # 信賴區間下界
    hi: float           # 信賴區間上界


@dataclass
class Recommendation:
    rule: RuleResult
    used_upper_bound: bool
    alternatives: list[dict] = field(default_factory=list)


def decide(fc: Forecast, group: str, intensity: str, engine: RuleEngine | None = None,
           alternatives: list[dict] | None = None) -> Recommendation:
    engine = engine or RuleEngine()
    point = engine.level_of(fc.aqi)
    upper = engine.level_of(fc.hi)
    # 預防原則：敏感族群且上界跨到較高等級時，採較高等級
    use_upper = group == "sensitive" and upper["min"] > point["min"]
    aqi_for_rule = fc.hi if use_upper else fc.aqi
    rule = engine.lookup(aqi_for_rule, group, intensity)
    return Recommendation(rule=rule, used_upper_bound=use_upper, alternatives=alternatives or [])


if __name__ == "__main__":
    rec = decide(Forecast(aqi=98, lo=83, hi=113), group="sensitive", intensity="vigorous")
    print(rec)
