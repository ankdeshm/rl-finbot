# Demo stories

The synthetic data contains five business stories. They let a demo show that the copilot finds
drivers that are actually in the numbers. All figures below are read from the generated tables
(`data/stories.json`, written by `scripts/generate_data.py`). The agent returns the same numbers;
see the saved answers in [`results/demo_responses/`](../results/demo_responses/). USD at budget
rate B26. As-of date 2026-11-12, so the last closed month is October 2026.

| # | Where | What happened | Question to ask |
|---|---|---|---|
| a | United States · Elevators & Pressure Vessels | 7A2 bonus spike in March 2025 | Break down 7A personnel cost for US Elevators & Pressure Vessels in March 2025 |
| b | Brazil · Environmental Lab Testing | Lost contract in Feb 2026; staff cut with a 3-month lag; restructuring charge | Why did Brazil Environmental Lab Testing margin drop in 2026? |
| c | Mexico · Buildings & Infrastructure | WIP build-up Jan–Jun 2026, reversal Jul–Sep 2026 | What happened to WIP in Mexico Buildings & Infrastructure this year? |
| d | Chile · Metals & Minerals | External subcontracting far above budget in 2026 | Why is Chile Metals & Minerals subcontracting above budget? |
| e | Canada · Power & Utilities | Steady margin improvement 2022–2025 | How has the MAOP margin of Canada Power & Utilities developed since 2022? |

## a. US Elevators & Pressure Vessels: bonus spike (March 2025)

| Item | March 2025 | March 2024 |
|---|---:|---:|
| 7A2 Bonus | USD 593.2k | USD 159.9k |
| 7A Direct labor cost | USD 2.02M | USD 1.54M |

- The March 2025 bonus is 3.7× March 2024. The average bonus in the other months of 2025 is USD 125.0k.
- In the 7A breakdown, the bonus explains 90.6% of the USD 478k increase in direct labor cost vs PY.

## b. Brazil Environmental Lab Testing: lost contract (2026)

| YTD October | 2026 Actual | 2025 Actual (PY) | 2026 Budget |
|---|---:|---:|---:|
| Production | USD 34.8M | USD 40.2M | USD 43.5M |
| Personnel charges | USD 17.6M | USD 18.5M | USD 19.9M |
| MAOP | USD 0.92M | USD 5.01M | USD 5.67M |
| MAOP margin (on revenue) | 2.6% | 12.5% | |
| Utilization rate | 75.6% | 81.8% | |

- Production is 13.5% below PY and 20.0% below budget.
- Personnel adjusts only from May 2026, which is three months after the volume loss.
- A one-off restructuring charge of USD 937k (account 17.1) is booked in May 2026.
- The margin bridge vs PY shows that personnel, other costs and functional costs are each a much larger share of a smaller revenue.

## c. Mexico Buildings & Infrastructure: WIP build-up and reversal (2026)

| Period | WIP change (account 2.1) |
|---|---:|
| Jan–Jun 2026 (build-up) | +USD 3.46M |
| Jul–Sep 2026 (reversal) | −USD 3.28M |
| YTD Oct 2026 | +USD 0.13M |
| YTD Oct 2025 | +USD 0.67M |

Billing jumps from about USD 3.2–3.5M a month in H1 to USD 4.2–5.0M a month in Jul–Oct, when the work in progress is invoiced.

The agent reports AD50 line 2 "WIP & UI", which is account 2.1 plus 2.2 (unearned income). On that line its trend answer shows: Jan–Jun 2026 +USD 3.4M (positive every month), Jul–Oct 2026 −USD 3.3M (negative every month), YTD +USD 108k.

## d. Chile Metals & Minerals: subcontracting above budget (2026)

| YTD October | Value |
|---|---:|
| External subcontracting, Actual 2026 | USD 363.6k |
| External subcontracting, Budget 2026 | USD 270.6k (Actual is 34.4% above budget) |
| External subcontracting, Actual 2025 | USD 255.0k (2026 is 42.6% above PY) |
| Subcontracting as % of production | 5.7% (2026) vs 4.2% (2025) |
| MAOP, Actual vs Budget | USD 704.7k vs USD 925.4k |

## e. Canada Power & Utilities: margin improvement

| MAOP margin (on revenue) | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|
| Full year | 9.2% | 11.4% | 12.3% | 14.7% | |
| YTD October | 8.9% | 11.8% | 12.5% | 14.8% | 14.6% |

The margin improves from 2022 to 2025 and is flat in 2026. The YTD October rows compare like for like with the current year.

## Group context (FY 2025)

| Metric | Value |
|---|---:|
| Production | USD 1,325.4M |
| MAOP | USD 187.3M (14.2% of revenue) |
| Net income | USD 120.6M |
| Direct margin | 60.7% |
| Utilization rate | 81.9% |
| Average FTE / headcount | 15,141 / 16,142 |
