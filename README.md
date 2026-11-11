# AirWise：空氣品質健康顧問 AI Agent

AirWise 是一個 Domain AI Agent：使用者用自然語言問「明早 7 點帶氣喘的孩子去公園跑 30 分鐘安全嗎？」，
AirWise 會取得最近測站的即時空品與氣象預報、預測目標時段 AQI、依台灣環境部 AQI 活動建議做出決策，
最後由 LLM 解釋結果並附上依據（測站、資料時間、規則條目、文件來源）。

> 狀態：Proposal 階段。目前為專案骨架，功能將依 DESIGN.md 的時程逐步實作。

## 專業摘要

臺灣規律運動人口於 2025 年達 35.6%，創 2014 年以來新高；然而大型世代研究顯示，當 PM2.5 年均濃度超過 25 μg/m³ 時，規律運動降低死亡風險的效益將由約 30% 降至 12–15%。民眾安排晨跑或戶外活動時，現有空品系統僅被動呈現即時與歷史監測值，缺乏可靠的短期趨勢推估，也無法將數據轉化為符合個人敏感度與活動強度的具體建議；若直接詢問大型語言模型（LLM），臨床情境研究顯示其幻覺率高達 50–82%，即使加入防幻覺提示仍有約 44%。

為此，本專題提出 AirWise，一個規則錨定、工具導向的空氣品質健康顧問 AI Agent。系統以 OpenAI 白名單 Function Calling 串接環境部 AQI 與中央氣象署預報資料，以 XGBoost 與 LSTM 進行 1 至 24 小時 AQI 預測，並以 split conformal prediction 估計信賴區間。決策階段依環境部 AQI 活動建議建構「等級 × 族群 × 活動強度」規則庫，對敏感族群採預測上界之預防原則，理論上可將低估警示機率控制在 α 以內。LLM 僅負責解析問題與解釋結果，回答須附測站、資料時間與規則來源；引用檢查失敗，或遇資料中斷、用藥與診斷等越界請求時，系統即安全降級。

評估規劃以臺中測站 2023–2025 年逐時資料進行滾動回測，並以 50 題含異常與越界情境的在地問答集，比較純 LLM 與資料增強 LLM 兩種基線，輔以線上問卷。預期 AirWise 在 6–24 小時預測之 MAE 與 RMSE 較持續法改善 10% 以上，來源揭露率與安全降級率達 100%，並在指引一致率與幻覺率上優於基線；上述皆為待驗證之預期目標。本專題的貢獻在於以系統架構而非提示詞約束 LLM，並將預測不確定性轉化為可驗證、可追溯的個人化健康行為建議。

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
