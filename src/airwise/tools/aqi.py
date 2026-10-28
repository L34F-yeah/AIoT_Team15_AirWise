"""④ Data Acquisition：環境部 AQI 開放資料（aqx_p_432）。

API 說明：https://data.moenv.gov.tw/paradigm
需要環境變數 MOENV_API_KEY（註冊會員後取得）。

    python -m airwise.tools.aqi --county 臺中市
"""
from __future__ import annotations

import argparse
import math
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
STALE_AFTER = timedelta(hours=2)


def fetch_latest(limit: int = 1000) -> list[dict]:
    key = os.getenv("MOENV_API_KEY")
    if not key:
        raise RuntimeError("請在 .env 設定 MOENV_API_KEY")
    resp = requests.get(API_URL, params={"api_key": key, "format": "json", "limit": limit}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    # API 回傳格式可能是 list 或 {"records": [...]}，兩種都處理
    return data["records"] if isinstance(data, dict) and "records" in data else data


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def is_valid(record: dict, now: datetime | None = None) -> bool:
    """資料品質檢查：AQI 為數值，且發布時間在 2 小時內。"""
    if _num(record.get("aqi")) is None:
        return False
    try:
        t = datetime.strptime(record.get("publishtime", ""), "%Y/%m/%d %H:%M:%S")
    except ValueError:
        return False
    return (now or datetime.now()) - t <= STALE_AFTER


def nearest_stations(records: list[dict], lat: float, lon: float, k: int = 3) -> list[dict]:
    """依直線距離排序，回傳最近 k 個測站（供例外時換站重試）。"""
    def dist(r: dict) -> float:
        rlat, rlon = _num(r.get("latitude")), _num(r.get("longitude"))
        if rlat is None or rlon is None:
            return math.inf
        dx = (rlon - lon) * 111.32 * math.cos(math.radians(lat))
        dy = (rlat - lat) * 110.57
        return math.hypot(dx, dy)

    ranked = sorted(records, key=dist)
    return [dict(r, distance_km=round(dist(r), 1)) for r in ranked[:k]]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--county", default="臺中市")
    a = p.parse_args()
    for r in fetch_latest():
        if r.get("county") == a.county:
            flag = "" if is_valid(r) else "（資料無效或過期）"
            print(f"{r.get('sitename')}: AQI {r.get('aqi')} {r.get('status')} "
                  f"PM2.5 {r.get('pm2.5')} @ {r.get('publishtime')}{flag}")


if __name__ == "__main__":
    main()
