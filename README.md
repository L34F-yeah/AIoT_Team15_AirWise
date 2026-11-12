# AirWise：空氣品質健康顧問 AI Agent

AirWise 是一個 Domain AI Agent：使用者用自然語言問「明早 7 點帶氣喘的孩子去公園跑 30 分鐘安全嗎？」，
AirWise 會取得最近測站的即時空品與氣象預報、預測目標時段 AQI、依台灣環境部 AQI 活動建議做出決策，
最後由 LLM 解釋結果並附上依據（測站、資料時間、規則條目、文件來源）。

> 狀態：Proposal 階段。目前為專案骨架，功能將依 DESIGN.md 的時程逐步實作。

## 專業摘要

臺灣規律運動人口於 2025 年達 35.6% 創新高，但 PM2.5 年均超過 25 μg/m³ 時，運動降低死亡風險的效益會由約 30% 降至 12–15%。現有空品系統只顯示即時數值，無法依個人敏感度與活動強度給建議；直接詢問 LLM 則有 50–82% 的幻覺率。本專題提出 AirWise，一個規則錨定、工具導向的空品健康 AI Agent：串接環境部與氣象署資料，以 XGBoost 與 LSTM 預測 1–24 小時 AQI 並以 conformal prediction 估計區間，再依官方「等級 × 族群 × 強度」規則庫決策，對敏感族群採預測上界。LLM 只負責理解與解釋，回答必附測站、時間與規則來源，越界請求即安全降級。評估以臺中測站資料回測及 50 題問答集進行，預期成果皆待驗證。

**關鍵詞**：AI Agent、空氣品質指標、時間序列預測、Conformal Prediction、幻覺防護、健康風險溝通

> 摘要中的數據來源與完整參考文獻見 [docs/research/](docs/research/AirWise_研究論述_證據預期貢獻與摘要.pdf)。

## 功能（規劃）

- 自然語言問答，缺資訊時主動反問
- 即時 AQI（環境部 aqx_p_432）與鄉鎮天氣預報（中央氣象署 F-D0047）
- 1–24 小時 AQI 預測與信賴區間（Persistence / XGBoost / LSTM）
- 規則庫：AQI 等級 × 族群 × 活動強度 → 建議
- RAG 引用官方健康指引；引用檢查失敗時改用模板回答

## Installation

```bash
git clone https://github.com/L34F-yeah/AIoT_Team15_AirWise.git
cd AIoT_Team15_AirWise
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # 填入 API 金鑰
```

需要的金鑰：

| 變數 | 取得方式 |
| --- | --- |
| `MOENV_API_KEY` | 環境部資料開放平臺註冊會員：https://data.moenv.gov.tw/ |
| `CWA_API_KEY` | 中央氣象署氣象資料開放平臺「取得授權碼」：https://opendata.cwa.gov.tw/ |
| `OPENAI_API_KEY` | OpenAI 平台 API Keys 頁面：https://platform.openai.com/ |

## How to Run

```bash
# 1. 測試資料工具：印出台中市各測站即時 AQI
python -m airwise.tools.aqi --county 臺中市

# 2. 測試規則引擎（不需 API）
python -m airwise.rules.engine --aqi 128 --group sensitive --intensity vigorous

# 3. 啟動聊天介面（W3 之後）
streamlit run app/main.py

# 4. 執行評測（W6 之後）
python eval/run_eval.py --qa eval/qa_set.jsonl
```

## Repository 結構

```
AIoT_Team15_AirWise/
├── README.md            專題介紹、安裝、執行、Demo
├── DESIGN.md            系統設計文件（持續更新）
├── requirements.txt
├── .env.example
├── data/                資料說明與下載腳本（大型原始檔不進版控）
├── knowledge/           aqi_rules.yaml、官方指引文件
├── src/airwise/         agent、tools、forecast、rules、rag
├── eval/                qa_set.jsonl、評測腳本、結果
├── app/                 Streamlit 介面
└── docs/                架構圖、流程圖、簡報
```

## Demo

（期末補上 YouTube 影片連結與截圖）

## 免責聲明

AirWise 提供的是依公開資料與官方指引產生的一般性建議，不能取代醫療專業意見。
