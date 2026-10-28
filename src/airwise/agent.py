"""③ Planner & Reasoning Agent（骨架，W3 實作）。

流程對應 Proposal 的 Algorithm 1：
  parse_query → (缺資訊則反問) → 取資料 → 預測 → 決策 → 解釋 → 引用檢查
LLM 只負責 parse_query 與 explain；等級與建議一律來自 decision / rules。
"""
from __future__ import annotations

REQUIRED_SLOTS = ("location", "time", "activity", "intensity")


def parse_query(query: str, profile: dict) -> dict:
    """用 LLM Tool Calling 把問題轉成 slots。TODO(W3)。"""
    raise NotImplementedError


def missing_slots(slots: dict) -> list[str]:
    return [s for s in REQUIRED_SLOTS if not slots.get(s)]


def run(query: str, profile: dict) -> dict:
    """主流程。TODO(W3–W5)：串接 tools、forecast、decision、output。"""
    slots = parse_query(query, profile)
    if missing := missing_slots(slots):
        return {"type": "clarify", "missing": missing}
    raise NotImplementedError
