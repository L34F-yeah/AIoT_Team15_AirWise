"""⑥ Domain Knowledge：AQI 規則引擎。

依 AQI 數值、族群與活動強度，從 knowledge/aqi_rules.yaml 查出建議與規則 ID。
此模組不依賴任何 API，可直接測試：

    python -m airwise.rules.engine --aqi 128 --group sensitive --intensity vigorous
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml

RULES_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "aqi_rules.yaml"


@dataclass
class RuleResult:
    level_id: str
    level_name: str
    rule_id: str
    action: str
    advice: str
    verified: bool


class RuleEngine:
    def __init__(self, path: Path = RULES_PATH):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.levels = data["levels"]
        self.rules = data["rules"]

    def level_of(self, aqi: float) -> dict:
        aqi = max(0, round(aqi))
        for lv in self.levels:
            if lv["min"] <= aqi <= lv["max"]:
                return lv
        return self.levels[-1]  # > 500 視為最高等級

    def lookup(self, aqi: float, group: str, intensity: str) -> RuleResult:
        lv = self.level_of(aqi)
        candidates = [r for r in self.rules if r["level"] == lv["id"]]

        def score(r: dict) -> int | None:
            # 越具體的規則分數越高；不相符回傳 None
            s = 0
            for key, value in (("group", group), ("intensity", intensity)):
                if r[key] == value:
                    s += 2
                elif r[key] == "*":
                    s += 0
                else:
                    return None
            return s

        scored = [(score(r), r) for r in candidates]
        scored = [(s, r) for s, r in scored if s is not None]
        if not scored and group == "student":
            # 學生沒有專屬規則時，退回一般民眾規則
            return self.lookup(aqi, "general", intensity)
        if not scored:
            raise LookupError(f"規則庫缺少 {lv['id']} / {group} / {intensity} 的規則")
        _, best = max(scored, key=lambda x: x[0])
        return RuleResult(lv["id"], lv["name"], best["id"], best["action"],
                          best["advice"], best.get("verified", False))


def main() -> None:
    p = argparse.ArgumentParser(description="查詢 AQI 規則")
    p.add_argument("--aqi", type=float, required=True)
    p.add_argument("--group", default="general", choices=["general", "sensitive", "student"])
    p.add_argument("--intensity", default="moderate", choices=["light", "moderate", "vigorous"])
    a = p.parse_args()
    r = RuleEngine().lookup(a.aqi, a.group, a.intensity)
    print(f"AQI {a.aqi:.0f} → {r.level_name}（{r.level_id}）")
    print(f"規則 {r.rule_id}：{r.advice}  [action={r.action}, verified={r.verified}]")


if __name__ == "__main__":
    main()
