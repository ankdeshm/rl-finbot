# Demo stories

The synthetic data contains five business stories. They let a demo show that the copilot finds
drivers that are actually in the numbers. All figures below are read from the generated tables
(`data/stories.json`, written by `scripts/generate_data.py`). The agent returns the same numbers;
see the saved answers in [`results/demo_responses/`](../results/demo_responses/). USD at a constant
budget rate. As-of date 2026-11-12, so the last closed month is October 2026.

| # | Where | What happened | Question to ask |
|---|---|---|---|
| a | United States · Elevators & Pressure Vessels | Direct staff bonus spike in March 2025 | Break down direct staff costs for US Elevators & Pressure Vessels in March 2025 |
| b | Canada · Environmental Lab Testing | Lost contract in Feb 2026; staff cut with a 3-month lag (restructuring leavers in April, restructuring charge in May) | Why did Canada Environmental Lab Testing margin drop in 2026? · Attrition by role for Canada Environmental Lab Testing this year vs last year |
| c | Mexico · Buildings & Infrastructure | WIP build-up Jan–Jun 2026, reversal Jul–Sep 2026 | What happened to WIP in Mexico Buildings & Infrastructure this year? |
| d | Chile · Metals & Minerals | External subcontracting far above budget in 2026 | Why is Chile Metals & Minerals subcontracting above budget? |
| e | Canada · Power & Utilities | Steady margin improvement 2022–2026 | How has the operating margin of Canada Power & Utilities developed since 2022? |

## a. US Elevators & Pressure Vessels: bonus spike (March 2025)

| Item | March 2025 | March 2024 |
|---|---:|---:|
| Direct staff bonus | USD 472.4k | USD 159.1k |
| Direct staff costs | USD 1.61M | USD 1.27M |

- The March 2025 bonus is 2.97× March 2024. The average bonus in the other months of 2025 is USD 99.9k.
- In the direct staff cost breakdown, the bonus explains 91.5% of the USD 342k increase vs PY.

## b. Canada Environmental Lab Testing: lost contract (2026)

| YTD October | 2026 Actual | 2025 Actual (PY) | 2026 Budget |
|---|---:|---:|---:|
| Production | USD 53.7M | USD 62.6M | USD 67.7M |
| Personnel costs | USD 27.0M | USD 28.6M | USD 30.8M |
| Operating profit | USD 1.57M | USD 7.88M | USD 8.92M |
| Operating margin (on revenue) | 2.9% | 12.7% | |
| Utilization rate | 67.9% | 73.9% | |

- Production is 14.2% below PY and 20.8% below budget.
- Personnel costs adjust only from May 2026 (about USD 2.9–3.1M a month in Jan–Apr, about USD 2.5M from May), three months after the volume loss.
- A one-off restructuring charge of USD 1.44M (other operating expenses) is booked in May 2026.
- The margin bridge vs PY shows that personnel, other costs and functional costs are each a much larger share of a smaller revenue.

The employee records tell the same story:

| YTD October | 2026 | 2025 (PY) |
|---|---:|---:|
| Average headcount | 353 | 382 |
| Hires | 48 | 44 |
| Leavers (voluntary / restructuring) | 99 (37 / 62) | 32 (29 / 3) |
| Attrition rate, annualised | 33.6% | 10.1% |

- 60 of the 62 restructuring leavers leave in April 2026.
- Utilization by role, YTD 2026: lab analyst 68.3%, lab technician 67.8%, chemist 67.4%.

## c. Mexico Buildings & Infrastructure: WIP build-up and reversal (2026)

| Period | WIP change (account 2.1) |
|---|---:|
| Jan–Jun 2026 (build-up) | +USD 835k |
| Jul–Sep 2026 (reversal) | −USD 793k |
| YTD Oct 2026 | +USD 41k |
| YTD Oct 2025 | +USD 168k |

Billing rises from about USD 0.74–0.88M a month in H1 to USD 1.02–1.20M a month in Jul–Oct, when the work in progress is invoiced.

The agent reports the P&L line "WIP & deferred income", which is account 2.1 plus the deferred income change (account 2.2). On that line its trend answer shows: Jan–Jun 2026 +USD 822k (positive every month), Jul–Sep 2026 −USD 783k (negative every month), YTD +USD 42k.

## d. Chile Metals & Minerals: subcontracting above budget (2026)

| YTD October | Value |
|---|---:|
| External subcontracting, Actual 2026 | USD 2.80M |
| External subcontracting, Budget 2026 | USD 2.08M (Actual is 34.6% above budget) |
| External subcontracting, Actual 2025 | USD 1.97M (2026 is 42.4% above PY) |
| Subcontracting as % of production | 5.4% (2026) vs 4.0% (2025) |
| Operating profit, Actual vs Budget | USD 5.68M vs USD 7.06M |

## e. Canada Power & Utilities: margin improvement

| Operating margin (on revenue) | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|
| Full year | 10.10% | 10.80% | 12.35% | 13.14% | |
| YTD October | 10.13% | 11.10% | 12.75% | 13.19% | 14.31% |

The margin improves every year. The YTD October rows compare like for like with the current year.

## Group context (FY 2025)

| Metric | Value |
|---|---:|
| Production | USD 1,386.3M |
| Operating profit | USD 195.2M (14.1% of revenue) |
| Net income | USD 127.2M |
| Direct margin | 59.4% |
| Utilization rate | 74.0% |
| Average FTE / headcount | 15,455 / 16,473 |
| Hires / leavers (voluntary / restructuring) | 2,513 / 2,211 (2,085 / 126) |
| Attrition rate | 13.4% |
