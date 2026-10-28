# CLAUDE.md — AirWise 專案說明（給 Claude Code 讀）

## 專案是什麼

AirWise 是課程期末專題：一個空氣品質健康顧問 Domain AI Agent。
使用者用中文自然語言問「某族群在某時段做某強度活動安不安全」，系統取得台灣環境部即時 AQI 與中央氣象署預報、
預測目標時段 AQI、依台灣 AQI 活動建議規則做決策，最後由 LLM 解釋並附上依據。

完整設計在 `DESIGN.md`，執行方式在 `README.md`。開始任何工作前先讀這兩個檔案。

## 核心設計原則（不可違反）

1. **LLM 只做兩件事**：把問題轉成結構化 slots（地點、時段、活動、強度），以及把決策結果轉成自然語言。
   AQI 數值、等級、建議一律來自 `tools/`、`forecast/`、`rules/`、`decision.py`，不可讓 LLM 自己產生。
2. **預防原則**：敏感族群且預測上界跨到較高等級時，採較高等級（`decision.py`）。
3. **可追溯**：每個回答都要帶 Evidence：測站、資料時間、預測值與區間、規則 ID、文件來源。
4. **引用檢查失敗就改用模板回答**，不能讓未經驗證的 LLM 文字輸出給使用者。
5. 回答必附免責聲明：不能取代醫療專業意見。

## 程式結構

| 路徑 | 模組 | 對應 Pseudocode |
| --- | --- | --- |
| `src/airwise/agent.py` | ③ Planner，主流程 | 01–04、23–26 |
| `src/airwise/tools/aqi.py` | ④ 環境部 AQI（aqx_p_432） | 05–09 |
| `src/airwise/tools/weather.py` | ④ 氣象署 F-D0047-075 | 10 |
| `src/airwise/forecast/` | ⑤ Persistence / XGBoost / LSTM | 11–14 |
| `src/airwise/decision.py` | ⑦ 預防原則、建議合成 | 15–17、20–22 |
| `src/airwise/rules/engine.py` + `knowledge/aqi_rules.yaml` | ⑥ 規則庫 | 18 |
| `src/airwise/rag/` | ⑥ RAG 官方指引 | 19 |
| `src/airwise/output.py` | ⑧ 解釋、引用檢查 | 23–24 |
| `app/main.py` | Streamlit 介面 | 25 |
| `eval/` | E1 預測、E2 50 題問答、E3 線上問卷 | — |

## 開發時程（8 週）

W1 API 金鑰、歷史資料下載腳本 → W2 即時 AQI + 規則最小版本 → W3 LLM Planner + Tool Calling →
W4 預測模型與 E1 → W5 RAG、引用檢查、預防原則 → W6 50 題問答集、E2、消融 → W7 線上問卷 E3 → W8 文件、PPT、影片。

## 開發規則

- 語言：程式註解與使用者介面用繁體中文；變數與函式名稱用英文。
- Python 3.10+，用 `pip install -e .` 安裝；套件在 `src/airwise/`。
- LLM 使用 OpenAI API（官方 `openai` 套件，function calling 實作 Tool Calling）；金鑰 `OPENAI_API_KEY`、模型 `OPENAI_MODEL` 從 `.env` 讀取，不寫死在程式裡。
- API 金鑰只放 `.env`，絕不寫進程式或 commit。
- 大型資料放 `data/raw/`（已在 .gitignore），以腳本重現。
- 每完成一個模組：寫最少一個可執行的測試或 `python -m` 範例，並更新 `DESIGN.md` 的 Components 狀態與 Implementation Mapping。
- 實驗結果只寫實際跑出來的數字，不可估計或虛構。
- `knowledge/aqi_rules.yaml` 的建議文字必須與環境部原文一致；未核對的規則保持 `verified: false`。

## 快速檢查

```bash
python -m airwise.rules.engine --aqi 128 --group sensitive --intensity vigorous
python -m airwise.decision
python -m airwise.tools.aqi --county 臺中市   # 需要 MOENV_API_KEY
```
