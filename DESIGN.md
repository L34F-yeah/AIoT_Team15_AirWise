# AirWise DESIGN.md

> 本文件從 Proposal 階段開始維護，每完成一個模組就更新對應章節。
> 目標：即使原開發者不在，下一位開發者也能透過 GitHub + README.md + DESIGN.md 理解、執行、驗證並繼續開發。

| 版本 | 日期 | 內容 |
| --- | --- | --- |
| v0.1 | 2026-10-28 | Proposal 階段初版：問題、需求、架構、演算法、資料與評估計畫 |

---

## 1. Problem

使用者能取得 AQI 數字，但真正需要的是「我（某族群）在某時段做某活動（某強度）安不安全、該怎麼調整」。
這需要三件事同時成立：未來時段的空品推估、個人敏感度判斷、官方指引的正確套用。
直接問 LLM 會得到沒有資料依據的回答（幻覺）。

## 2. Requirements

### 功能需求

| ID | 需求 | 優先 |
| --- | --- | --- |
| FR1 | 解析自然語言問題，抽出地點、時段、活動、強度 | Must |
| FR2 | 缺少必要資訊時反問使用者 | Must |
| FR3 | 取得最近測站即時 AQI 與鄉鎮天氣預報 | Must |
| FR4 | 預測 1–24 小時後 AQI 與信賴區間 | Must |
| FR5 | 依 AQI 等級 × 族群 × 活動強度查規則產生建議 | Must |
| FR6 | 建議附依據：測站、資料時間、規則 ID、文件來源 | Must |
| FR7 | 提供替代時段（未來 12 小時內較佳時段） | Should |
| FR8 | 引用檢查失敗時改用模板回答 | Must |
| FR9 | 收集使用者回饋 | Could |

### 非功能需求

- 回應時間：一般問題 10 秒內
- 可追溯：每次回答記錄輸入、工具呼叫、規則 ID、輸出
- 安全：回答必附免責聲明；API 金鑰不得進版控

## 3. Architecture

```
① User Scenario → ② Query + Profile → ③ Planner Agent (LLM)
                                          │ Tool Calling
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             ④ Data Acquisition → ⑤ Analytics Engine   ⑥ Domain Knowledge
               (MOENV, CWA API)    (forecast + CI)       (rules + RAG)
                                          │                     │
                                          └──────► ⑦ Decision ◄─┘
                                                       │
                                                ⑧ Output & Interaction → back to ①
```

完整架構圖與流程圖：見 Proposal 文件 4.1、4.2（期末匯出到 `docs/`）。

## 4. Components

| 模組 | 程式位置 | 職責 | 狀態 |
| --- | --- | --- | --- |
| ② Query + Profile | `src/airwise/profile.py` | 使用者 Profile 結構 | 骨架 |
| ③ Planner Agent | `src/airwise/agent.py` | LLM 解析意圖、Tool Calling、反問 | 骨架 |
| ④ Data Acquisition | `src/airwise/tools/aqi.py`、`tools/weather.py` | API 取資料、快取、品質檢查 | 骨架 |
| ⑤ Analytics Engine | `src/airwise/forecast/` | Persistence / XGBoost / LSTM 預測 | 未開始 |
| ⑥ Domain Knowledge | `knowledge/aqi_rules.yaml`、`src/airwise/rules/`、`src/airwise/rag/` | 規則查詢、文件檢索 | 規則骨架 |
| ⑦ Decision | `src/airwise/decision.py` | 預防原則、替代時段、合成建議 | 骨架 |
| ⑧ Output | `src/airwise/output.py`、`app/main.py` | 回答生成、引用檢查、介面 | 未開始 |

## 5. Data

| 資料 | 來源 | 用途 | 更新頻率 |
| --- | --- | --- | --- |
| 即時 AQI（aqx_p_432） | 環境部資料開放平臺 API v2 | 現況、預測輸入 | 每小時 |
| 歷史 AQI（依年月下載） | 環境部資料開放平臺（`year_month` 參數） | 訓練與測試預測模型 | 每月 |
| 鄉鎮天氣預報（臺中市 F-D0047-075） | 中央氣象署開放資料 | 預測特徵（風速、濕度、降雨） | 每 6 小時 |
| AQI 健康影響與活動建議 | 環境部空品監測網 | 規則庫、RAG 文件 | 制度修訂時 |

資料切分：台中市測站（西屯、忠明、大里等）2023–2024 訓練、2025 測試。
大型原始檔不進版控，以 `data/download.py` 重現。

## 6. AI / Analytics

- **LLM（③⑧）**：使用 OpenAI API（function calling），金鑰為 `OPENAI_API_KEY`，模型名稱設定在 `.env` 的 `OPENAI_MODEL`。只做兩件事：把問題轉成結構化參數、把決策結果轉成自然語言。不得自行產生 AQI 數值或等級。
- **預測（⑤）**：
  - Baseline 1：Persistence（下一時段 = 現在值）
  - Baseline 2：前一日同時段
  - 主模型：XGBoost（特徵：過去 24 小時污染物、時間特徵、風速風向、濕度、降雨機率）
  - 加分：LSTM
  - 信賴區間：以驗證集殘差分位數估計（quantile of residuals）

## 7. Domain Knowledge

- 規則庫：`knowledge/aqi_rules.yaml`，依台灣 AQI 六級 × 族群（general / sensitive / student）× 活動強度（light / moderate / vigorous）。
- 五個核心思維模式與對應設計（見 Proposal 第 3 節）：
  1. 劑量思維 → 輸入含活動強度與時長
  2. 族群差異 → Profile 標記族群
  3. 權衡思維 → 給替代方案而非一律取消
  4. 預防原則 → 預測上界跨級且為敏感族群時採較高等級
  5. 時空變異 → 用最近測站逐時資料，兼看臭氧
- 規則條文需逐條對照環境部空品監測網原文，並在 YAML 中記錄 `source`。

## 8. Algorithm

見 Proposal 文件 4.3 Algorithm 1（26 行）。關鍵行：
- 03–04：缺資訊反問（Human Interaction 迴圈）
- 07–09：資料例外處理
- 16–17：預防原則
- 23–24：LLM 只能使用 R 與 E；引用檢查失敗改用模板

## 9. Implementation Mapping

| Pseudocode 行 | 函式 |
| --- | --- |
| 02 | `agent.parse_query()` |
| 05–09 | `tools.aqi.nearest_station()`、`tools.aqi.fetch_latest()` |
| 10 | `tools.weather.fetch_forecast()` |
| 13 | `forecast.predict()` |
| 15–17 | `decision.decide_level()` |
| 18 | `rules.engine.lookup()` |
| 19 | `rag.retrieve()` |
| 20–22 | `decision.compose()` |
| 23–24 | `output.explain()`、`output.citation_check()` |

## 10. How to Run

見 README.md。

## 11. Evaluation Plan → Results

| 實驗 | Metrics | 結果 |
| --- | --- | --- |
| E1 預測 | MAE、RMSE、等級 Macro-F1 | 待實驗 |
| E2 建議品質（50 題） | 指引一致率、幻覺率、引用正確率、反問正確率 | 待實驗 |
| E3 線上問卷（Google 表單，≥20 份，5 個情境，AirWise vs 環境即時通截圖） | 偏好比例、決策信心、資訊清楚度、開放意見 | 待實驗 |
| 消融 | 拿掉預測 / 規則 / RAG / 引用檢查 | 待實驗 |

## 12. Limitations（目前已知）

- 測站密度有限，距離測站遠的地點誤差較大
- 規則庫只涵蓋官方指引，無法取代個人醫囑
- 第一版不使用微型感測器資料（準確度與校正問題）

## 13. Future Work

- 加入校正後的微型感測器資料
- 個人化回饋學習（依使用者症狀回報調整建議）
- LINE Bot 推播
