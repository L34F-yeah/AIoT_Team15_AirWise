"""④ Data Acquisition：中央氣象署鄉鎮天氣預報（臺中市 F-D0047-075，骨架，W1–W2 實作）。

需要環境變數 CWA_API_KEY（氣象資料開放平臺「取得授權碼」）。
API 文件：https://opendata.cwa.gov.tw/dist/opendata-swagger.html
"""
from __future__ import annotations

DATASET_ID = "F-D0047-075"  # 臺中市未來 1 週鄉鎮天氣預報


def fetch_forecast(town: str) -> dict:
    """回傳指定鄉鎮的逐時溫度、濕度、降雨機率、風速。TODO(W2)。"""
    raise NotImplementedError
