# AirWise: A Rule-Grounded, Tool-Oriented LLM Agent for Personalized Air-Quality Health Advice with Conformal Precautionary Decisions

**AIoT Final Project, Team 15**

*Manuscript draft, proposal stage, November 2026. All quantitative outcomes stated in this manuscript are pre-registered targets, not experimental results. Experimental results will replace them after the evaluation in Section V is completed.*

---

***Abstract*—Regular exercise participation in Taiwan reached 35.6% in 2025, the highest level since 2014. Yet large cohort evidence shows that when the annual mean PM2.5 concentration exceeds 25 μg/m³, the mortality-risk reduction associated with regular exercise falls from about 30% to 12–15%. People who plan outdoor activities only have access to real-time and historical monitoring values. Existing air-quality systems provide neither reliable short-term forecasts nor advice that accounts for individual sensitivity and activity intensity. Large language models (LLMs) can answer such questions conversationally, but clinical-scenario studies report hallucination rates of 50–82%, and about 44% even with mitigation prompts. This paper proposes AirWise, a rule-grounded, tool-oriented air-quality health advisory agent. AirWise uses whitelisted OpenAI function calling to access official data from Taiwan's Ministry of Environment and Central Weather Administration. It forecasts the air quality index (AQI) 1–24 h ahead with XGBoost and long short-term memory (LSTM) models and quantifies uncertainty with split conformal prediction. Decisions are made by a rule base that encodes official activity guidance as AQI level × population group × activity intensity. For sensitive groups, the rule base uses the upper bound of the prediction interval. We show that this precautionary rule bounds the probability of under-warning by the miscoverage level α under exchangeability. The LLM only parses queries and explains decisions. Every answer must cite the station, data timestamp, and rule identifier. Failed citation checks, data outages, and out-of-scope requests such as medication or diagnosis trigger safe degradation. The evaluation plan comprises rolling-origin backtesting on Taichung stations for 2023–2025, a 50-question local scenario benchmark compared against two LLM baselines, and an online user survey.*

***Index Terms*—AI agent, air quality index (AQI), time-series forecasting, conformal prediction, hallucination mitigation, health risk communication.**

---

## I. Introduction

Air pollution remains a major global health risk. The *State of Global Air 2025* report attributes about 7.9 million deaths in 2023 to air pollution [1]. In Taiwan, the national annual mean PM2.5 concentration fell to 12.8 μg/m³ in 2025, about 21% lower than in 2019 [6]. The government has set targets below 10 μg/m³ by 2030 and below 8 μg/m³ by 2035 [6], and has started PM0.1 ultrafine-particle monitoring in Taipei, Taichung, and Tainan from 2026 [12]. At the same time, physical activity is rising. The 2025 national sports survey (n = 25,472) reports a regular-exercise rate of 35.6%, the highest since 2014, and a participation rate of 83.3% [4].

These two trends interact. A cohort study of 1.5 million adults led by National Chung Hsing University in Taichung, in collaboration with University College London, found that exercising 2.5 h or more per week lowers mortality risk by about 30%. The benefit drops to 12–15% when the annual mean PM2.5 exceeds 25 μg/m³ [2]. Short-term exposure also matters: an analysis of more than 2.5 million finishing times from nine U.S. marathons associated each 1 μg/m³ increase in PM2.5 with slower finishing times of 32 s for men and 25 s for women [3]. Episodes still occur locally. Before the 2026 Lunar New Year, transboundary pollution combined with weak winds raised hourly PM2.5 in central and southern Taiwan to 35–45 μg/m³, and the authorities advised the public to "check the real-time air-quality app before going out" [5].

*However*, average improvement does not remove individual risk. More hours of weak wind and rising temperatures make ozone harder to reduce [7], and official forecasts acknowledge weather-driven uncertainty [5]. What a person needs is not a number but a decision: whether *this person*, at *this time*, doing *this intensity* of activity, is safe, and what to change if not. Existing tools leave that reasoning to the user. Readings from non-official low-cost sensors may also differ from those of standard monitoring stations [6].

*In the literature*, existing solutions fall into four categories, from oldest to newest.

1. **Real-time display systems** (official monitoring networks and AQI apps) provide trustworthy and widely available data. However, they show only current values, ignore individual sensitivity, and do not look ahead.
2. **Statistical and deep-learning forecasters**, including recent Transformer and iTransformer models for PM2.5 in Taiwan [13], [14], predict future concentrations. However, they output numbers only and do not produce health advice.
3. **LLM-based query and summarization agents** offer natural-language interaction. However, LLMs are unreliable in health settings: six models tested on 300 clinical scenarios hallucinated in 50–82% of cases, with a mean of 44% remaining after mitigation prompts [8]. Five popular chatbots gave problematic answers to 50% of health questions, with an average reference completeness of only 40% [9].
4. **Retrieval-augmented and tool-using domain agents** for environmental science [10], [11] ground answers in documents and data and reduce hallucination. However, they target experts or specific analysis tasks and do not combine short-term forecasting with individual sensitivity and official health rules.

The *key point* of this work is to constrain the LLM through architecture rather than prompting. The LLM only understands the query and explains the result. The decision is delegated to verifiable forecasting models and rules, and forecast uncertainty is converted into a conservative decision with a provable bound. The contributions of this paper are as follows.

- **C1 (System architecture):** A rule-grounded, tool-oriented agent with whitelisted tools and safe degradation, in which the LLM cannot generate AQI values, levels, or advice.
- **C2 (Method):** A precautionary level-decision rule based on split conformal intervals, with a proof that the under-warning probability for sensitive groups does not exceed α under exchangeability.
- **C3 (Domain knowledge):** A structured rule base that encodes the official AQI activity guidance as level × group × intensity, with a source annotated for each rule.
- **C4 (Benchmark):** A 50-question local air-quality health benchmark that includes at least 10 abnormal or out-of-scope scenarios, with reference answers and a scoring rubric.
- **C5 (Reproducibility):** An open-source system built only on public data, documented so that others can reproduce the forecasting (E1) and scenario-benchmark (E2) evaluations.

The rest of this paper is organized as follows. Section II reviews related work. Section III analyzes the domain reasoning that the system must encode. Section IV presents the proposed scheme, including its formulation, algorithm, worked example, and theoretical properties. Section V describes the experimental design and pre-registered targets. Section VI discusses limitations, and Section VII concludes the paper.

## II. Related Work

### A. Real-Time Air-Quality Information

Official monitoring networks publish hourly AQI values by station together with color-coded health guidance. These systems are authoritative and traceable, but they are passive. The user must interpret the number, project it to the planned time, and map it to their own sensitivity and activity. Official forecasts are issued at regional granularity and carry weather-driven uncertainty [5]. Low-cost sensors increase spatial coverage, but their readings may deviate from those of standard stations [6].

### B. Air-Quality Forecasting

Data-driven PM2.5 forecasting has moved from statistical models to deep architectures. Recent work applies attention-based Transformers [13] and iTransformer with large-scale atmospheric-pressure features to spatiotemporal PM2.5 prediction in Taiwan [14]. These studies evaluate numerical error, such as mean absolute error (MAE) and root mean square error (RMSE). They do not connect predictive uncertainty to downstream health decisions.

### C. LLMs in Health Communication

LLMs make health information accessible through dialogue, but their reliability is a concern. Omar *et al.* [8] showed that six LLMs hallucinated in 50–82% of adversarial clinical scenarios, and that a mitigation prompt reduced the mean rate only from 66% to 44%. A BMJ Open evaluation of five chatbots found problems in half of the health answers and incomplete references [9]. These findings motivate architectural rather than prompt-level safeguards.

### D. Domain-Specific LLM Agents

Emerging domain agents combine tool calling, knowledge retrieval, and auditable evidence chains. Examples include Emission-GPT for emission-inventory analysis [10] and TianJi-Environ, an autonomous agent for atmospheric environmental research [11]. These systems demonstrate the value of grounding LLMs in domain tools. However, they serve researchers and analysts rather than individuals making activity decisions.

### E. Comparison and Research Gap

Table I compares the four categories with AirWise on five criteria derived from the research gap. "Partial" entries are preliminary judgments based on published summaries and will be verified against the original papers.

**TABLE I**
**Comparison of Existing Approaches**

| Approach | Future-time forecast | Individual sensitivity | Official health rules | Traceable / hallucination-resistant | Quantitatively validated advice |
| --- | :---: | :---: | :---: | :---: | :---: |
| Real-time display | No | No | Partial | Yes | No |
| DL forecasting [13], [14] | Yes | No | No | No | No (numerical error only) |
| LLM query / summarization | No | Partial | Partial | Partial | Partial |
| Retrieval / tool-using agents [10], [11] | Partial | No | Yes | Yes | Partial |
| **AirWise (proposed)** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

No existing approach jointly provides 1) a short-term forecast with calibrated uncertainty, 2) personalization by sensitivity and intensity, 3) decisions anchored in official rules, and 4) a verifiable evidence chain for every answer. AirWise is designed to fill this gap.

## III. Domain Analysis

Answering "Is it safe for my asthmatic child to run tomorrow morning?" requires expert reasoning that the system must encode explicitly. We identify five reasoning patterns and map each to a design decision.

1. **Dose thinking:** exposure depends on concentration, duration, and ventilation rate. The query therefore includes activity intensity and duration.
2. **Population differences:** children, older adults, and people with cardiopulmonary conditions respond at lower concentrations. The user profile marks the population group.
3. **Trade-off thinking:** exercise has benefits that pollution reduces but does not eliminate [2]. The system therefore recommends alternatives (reschedule, reduce intensity, or move indoors) rather than a blanket prohibition.
4. **Precautionary principle:** under forecast uncertainty, sensitive groups should be protected against under-estimation. The system adopts the higher level when the interval's upper bound crosses a level boundary.
5. **Spatiotemporal variability:** pollution varies by location and hour, and ozone follows a different diurnal pattern from PM2.5 [7]. The system uses hourly data from the nearest station and considers ozone.

## IV. Proposed Scheme

### A. Design Paradigm

Conventional LLM assistants let the model answer the question. AirWise instead restricts the LLM to two roles: converting the question into structured slots and converting the decision into natural language. All AQI values, levels, and advice originate from forecasting models, the rule base, and the decision module.

### B. System Architecture

AirWise consists of eight modules (Fig. 1).

```
① User Scenario → ② Query + Profile → ③ Planner Agent (LLM)
                                          │ whitelisted tool calling
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             ④ Data Acquisition → ⑤ Analytics Engine   ⑥ Domain Knowledge
               (MOENV, CWA APIs)   (forecast + interval)  (rules + RAG)
                                          │                     │
                                          └──────► ⑦ Decision ◄─┘
                                                       │
                                                ⑧ Output & Interaction → ①
```

*Fig. 1. AirWise system architecture.*

- **② Query + Profile** stores the user's population group and preferences.
- **③ Planner Agent** uses OpenAI function calling to extract slots (location, target time, activity, intensity), asks follow-up questions when information is missing, and may call only predefined tools.
- **④ Data Acquisition** retrieves real-time AQI from the Ministry of Environment (MOENV) API (dataset aqx_p_432) and township forecasts from the Central Weather Administration (CWA) API (F-D0047-075). It also caches the data and checks its quality.
- **⑤ Analytics Engine** produces point forecasts and conformal prediction intervals.
- **⑥ Domain Knowledge** holds the YAML rule base and a retrieval module over official guidance documents.
- **⑦ Decision** applies the precautionary rule, looks up advice, and selects an alternative time slot.
- **⑧ Output & Interaction** generates the explanation, verifies citations, appends a medical disclaimer, and falls back to a template answer if verification fails.

### C. Problem Formulation

The LLM parses a user query $Q$ into a location, a target time $t$, a population group $g$, and an activity intensity $s$. Let $y$ denote the actual AQI at time $t$.

**AQI level function.** Taiwan's AQI has six levels with lower boundaries $b_0=0,\ b_1=51,\ b_2=101,\ b_3=151,\ b_4=201,\ b_5=301$:

$$
L(a) = \max\{\, k \in \{1,\dots,6\} : a \ge b_{k-1} \,\}. \tag{1}
$$

$L$ is monotonically non-decreasing: $a_1 \le a_2 \Rightarrow L(a_1) \le L(a_2)$.

**Forecast and prediction interval.** A forecaster $f$ (XGBoost or LSTM) yields a point prediction from features $\mathbf{x}_t$. These features are past pollutant concentrations, calendar features, wind speed and direction, humidity, and probability of precipitation. Using a held-out calibration set of size $n$, split conformal prediction sets

$$
\hat{y} = f(\mathbf{x}_t), \quad
q = \text{the } \lceil (n+1)(1-\alpha) \rceil\text{-th smallest of } \{|y_i - \hat{y}_i|\}_{i=1}^{n}, \quad
I = [\hat{y} - q,\ \hat{y} + q]. \tag{2}
$$

**Precautionary level decision.**

$$
L^{*} =
\begin{cases}
L(\hat{y} + q), & g = \text{sensitive},\\
L(\hat{y}), & \text{otherwise}.
\end{cases} \tag{3}
$$

**Advice and alternative slot.** Advice is retrieved from the rule base. The alternative slot is the time within the next 12 h that has the lowest level and is closest to the requested time:

$$
R = \mathrm{Rule}(L^{*}, g, s), \qquad
\tau^{*} = \arg\min_{\tau \in [t,\ t+12]} \big( L^{*}_{\tau},\ |\tau - t| \big), \tag{4}
$$

where the minimization is lexicographic.

### D. Rule Base

The rule base encodes the MOENV AQI health-impact and activity guidance as a table over six levels, three population groups (general, sensitive, student), and three intensities (light, moderate, vigorous). Each rule has an identifier (e.g., `R-L3-sensitive`), an action (ok, reduce, avoid, stay indoor), the advice text, its source, and a verification flag. Advice text must match the official wording. A rule remains marked unverified until it has been checked against the source. Because standards and indicators change (e.g., the introduction of PM0.1 monitoring [12]), the rule base is kept separate from the code so that it can be maintained and updated.

### E. Safe Degradation

AirWise falls back to a safe answer in four cases:

1. **Data outage:** if the nearest station fails, the system retries with the next-nearest station. If that also fails, it returns links to official sources instead of an answer.
2. **Missing information:** the planner asks a follow-up question instead of guessing.
3. **Citation failure:** if the generated text references values or rules absent from the evidence, the system outputs a deterministic template answer.
4. **Out-of-scope requests:** questions about medication or diagnosis are declined, and the user is advised to consult a medical professional.

### F. Algorithm

**Algorithm 1: AirWise Query Processing**

```
Input : user query Q, user profile P
Output: answer A with evidence E

 1  (loc, t, act, s) ← LLM.parse(Q);  g ← P.group
 2  while required slot missing do ask user; update slots
 3  st ← nearest_station(loc)
 4  D ← fetch_latest(st); if D fails then retry with next station
 5  if still unavailable then return official links (safe degradation)
 6  W ← fetch_forecast(loc)
 7  ŷ, q ← forecast(D, W, t)                      ▷ Eq. (2)
 8  L* ← L(ŷ + q) if g = sensitive else L(ŷ)      ▷ Eq. (3)
 9  R ← Rule(L*, g, s);  Doc ← RAG.retrieve(R)
10  τ* ← best alternative slot in [t, t+12]       ▷ Eq. (4)
11  E ← {st, data time, ŷ, I, rule ID, Doc}
12  A ← LLM.explain(R, τ*, E)                     ▷ LLM sees only R and E
13  if citation_check(A, E) fails then A ← template(R, τ*, E)
14  return A + E + medical disclaimer
```

### G. Illustrative Example

*The values in this example are hypothetical and are not experimental results.*

Query: "My child has asthma. Is it OK to run in a park in Xitun for 30 minutes at 7 a.m. tomorrow?"

1. *Parsing:* location = Xitun District, $t$ = 07:00 tomorrow, $g$ = sensitive, $s$ = vigorous. All slots are filled, so no follow-up question is needed.
2. *Data:* the nearest station is Xitun. The system reads its real-time AQI, the past 72 h of records, and the township forecast.
3. *Forecast:* suppose $\hat{y} = 98$ and $q = 15$, so $I = [83, 113]$.
4. *Precaution:* $L(98) = 2$ (moderate), but $L(113) = 3$ (unhealthy for sensitive groups). Because $g$ is sensitive, $L^{*} = 3$.
5. *Rule and alternative:* rule `R-L3-sensitive` advises reducing strenuous and outdoor activity. If the forecast for a later slot within the 12-h window falls to level 2, the system recommends that slot or an indoor workout.
6. *Output:* the LLM explains $R$ using only the evidence (station, data time, $\hat{y}$ and $I$, rule ID, document). The answer is released with a disclaimer after the citation check passes.

### H. Theoretical Properties

**Property 1 (Conservativeness).** For sensitive groups, $L^{*} \ge L(\hat{y})$.

*Proof:* Since $q \ge 0$, $\hat{y} + q \ge \hat{y}$, and the claim follows from the monotonicity of $L$. ∎

**Theorem 1 (Under-warning bound).** Suppose the calibration residuals and the test residual are exchangeable. Then, for sensitive groups, the probability that the issued level is lower than the true level is at most $\alpha$:

$$
P\big(L(y) > L^{*}\big) \le P\big(y > \hat{y} + q\big) \le P\big(|y - \hat{y}| > q\big) \le \alpha. \tag{5}
$$

*Proof:* If $y \le \hat{y} + q$, then $L(y) \le L(\hat{y} + q) = L^{*}$ by monotonicity, which gives the first inequality. The second holds because $\{y > \hat{y} + q\} \subseteq \{|y - \hat{y}| > q\}$. The third is the standard marginal coverage guarantee of split conformal prediction with the quantile index in (2). ∎

With $\alpha = 0.1$, the theoretical under-warning probability for sensitive groups is at most 10%.

**Remark.** Hourly air-quality series are autocorrelated and therefore not fully exchangeable, so Theorem 1 is a design rationale rather than a guarantee. Experiment E1 measures the empirical coverage and under-warning rate. Any deviation from the nominal level quantifies how far the exchangeability assumption is violated. Decreasing $\alpha$ lowers under-warning at the cost of wider intervals and more over-warning, a trade-off studied in Section V-E.

## V. Experimental Design

### A. E1: Forecasting Backtest

- **Data:** hourly observations from Taichung stations (Xitun, Zhongming, Dali, and others) for 2023–2025, optionally extended to 2026.
- **Split:** 2023–2024 for training, with a calibration subset held out from the training period, and 2025 for testing.
- **Protocol:** rolling-origin evaluation at horizons $h \in \{1, 6, 12, 24\}$ h.
- **Baselines:** persistence and same-hour-previous-day forecasts.
- **Models:** XGBoost and LSTM.
- **Metrics:** MAE, RMSE, AQI-level macro-F1, empirical interval coverage, and the under-warning rate for sensitive groups (to test Theorem 1).

### B. E2: Agent Scenario Benchmark

The benchmark has 50 local scenarios, at least 10 of which are abnormal or out-of-scope (data outage, missing information, medication or diagnosis requests). Three systems are compared: a plain LLM, an LLM with real-time data, and AirWise. The reference answers are derived from official guidance. The metrics are guideline-agreement rate, hallucination rate, citation accuracy, follow-up-question accuracy, source-disclosure rate, and safe-degradation rate. Two annotators label the outputs, and inter-annotator agreement is reported as Cohen's κ.

### C. E3: Online User Survey

At least 20 respondents compare AirWise outputs with screenshots of the official real-time air-quality app across five scenarios. The measures are preference ratio, decision confidence, clarity, and open-ended comments.

### D. Ablation Study

The forecaster, the rule base, the retrieval module, and the citation check are each removed in turn. The ablation shows which safeguard contributes most to agreement and to hallucination reduction.

### E. Experimental Setup and Parameter Study

The setup to be fixed and reported includes the missing-value handling, the OpenAI model version and temperature, the hardware, and the random seeds. The parameters to be studied are $\alpha \in \{0.05, 0.1, 0.2\}$, precaution on or off, retrieval depth $k \in \{1, 3, 5\}$, and a history window of 24 or 72 h. A plot of under-warning rate versus over-warning rate across $\alpha$ will characterize the precaution trade-off.

### F. Pre-Registered Targets

Following the course rule that proposal-stage experimental results must not be fabricated, Table II lists targets set in advance. These targets will be replaced with measured values.

**TABLE II**
**Pre-Registered Targets (Not Results)**

| Metric | Target |
| --- | --- |
| E1 forecast error | ≥ 10% MAE and RMSE improvement over persistence at 6–24 h horizons |
| E1 interval coverage | Empirical coverage close to 90% at α = 0.1 |
| E2 source disclosure | 100%: every recommendation cites station, data time, and rule ID |
| E2 safe degradation | 100%: all abnormal and out-of-scope cases correctly declined, clarified, or deferred |
| E2 agreement / hallucination | Higher agreement and lower hallucination than both LLM baselines |
| E3 user preference | Majority prefer AirWise and report higher decision confidence |

## VI. Discussion and Limitations

- **Station density:** accuracy degrades for locations far from a monitoring station. Calibrated low-cost sensors are a possible extension, but their readings require correction [6].
- **Exchangeability:** the bound in Theorem 1 relies on an assumption that hourly series only approximately satisfy. Its practical value must be established empirically in E1.
- **Scope of advice:** the rule base reflects official population-level guidance and cannot replace individual medical advice. Every answer therefore carries a disclaimer.
- **Survey validity:** E3 uses screenshots rather than live use, and the respondents are a convenience sample.

## VII. Conclusion

This paper presented AirWise, an air-quality health advisory agent that confines the LLM to understanding and explanation. AirWise grounds each decision in official data, calibrated forecasts, and an official rule base. The precautionary use of conformal upper bounds gives sensitive users a theoretically bounded under-warning probability. The evidence chain and safe-degradation paths make every answer traceable. The system is designed for planned activities by sensitive groups, such as scheduling a child's outdoor exercise. The evaluation in Section V will determine how far the pre-registered targets are met. Future work includes calibrated low-cost sensor integration, field user studies with live use, personalized feedback learning, and push notifications through a messaging bot.

## References

> References marked † were obtained through news coverage. They must be replaced with the original journal articles before formal submission.

[1] Health Effects Institute, "State of Global Air 2025," Boston, MA, USA, 2025.

[2] † Ku, Steptoe, and Zaninotto, *BMC Medicine*, 2025, as reported in "Air pollution may reduce health benefits of exercise," *UCL News*, Nov. 2025.

[3] † "How bad air quality slows down marathon runners," *Scientific American* (original study in *Sports Medicine*).

[4] † "運動部 2025 年運動現況調查" [2025 National Sports Survey by the Ministry of Sports], *PTS News Network*, Dec. 23, 2025.

[5] † "除夕東北季風增強挾境外污染物南下 全台空品亮橙燈" [Northeast monsoon brings transboundary pollution; orange air-quality alert nationwide on Lunar New Year's Eve], *United Daily News*, Feb. 12, 2026.

[6] † "環境部：國外報告空品排名定義遭誤解 台灣空氣品質全球排名進步中" [Ministry of Environment: Foreign report's air-quality ranking misinterpreted; Taiwan improving globally], *Economic Daily News*, Mar. 25, 2026.

[7] † "回顧 2025 空品監測 環境部：PM2.5 持續改善" [2025 air-quality monitoring review: PM2.5 continues to improve], *United Daily News*, Dec. 31, 2025.

[8] M. Omar *et al.*, "Multi-model assurance analysis showing large language models are highly vulnerable to adversarial hallucination attacks during clinical decision support," *Commun. Med.*, vol. 5, Art. no. 330, 2025, doi: 10.1038/s43856-025-01021-3.

[9] † "Substantial amount of medical information provided by popular chatbots inaccurate and incomplete," *BMJ Future Health*, May 15, 2026 (original study in *BMJ Open*).

[10] "Emission-GPT: A domain-specific language model agent for knowledge retrieval, emission inventory and data analysis," arXiv:2510.02359, 2025.

[11] "TianJi-Environ: An autonomous AI scientist for atmospheric environmental research," arXiv:2606.07697, 2026.

[12] † "環境部明年起啟動 PM0.1 超細懸浮微粒監測" [Ministry of Environment to launch PM0.1 ultrafine particle monitoring next year], *United Daily News*, Dec. 31, 2025.

[13] P.-Y. Kow and P.-E. Kow, "Transformers for air quality: Enhancing PM2.5 modelling with deep attention mechanisms," in *Proc. EGU General Assembly*, 2026, Abstract EGU26-1459.

[14] Y. Chuang and Y.-C. Lin, "Spatiotemporal prediction of PM2.5 in Taiwan using iTransformer and large-scale atmospheric pressure features," in *Proc. EGU General Assembly*, 2026, Abstract EGU26-6363.
