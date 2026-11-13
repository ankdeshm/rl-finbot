# Show personnel cost as % of revenue trend for Environmental Lab Testing since 2023

- **Persona:** Group CFO
- **Model:** `rules` · **status:** ok · **latency:** 0.14 s
- **Tool:** `get_trend` (chosen by `router_fallback`) · **numeric guardrail:** n/a (no LLM)

## Answer

**Personnel charges / Revenue monthly trend for Environmental Lab Testing, Jan 2023 - Oct 2026 (series: Actual, Actual R12M, Budget), USD.**

- Actual by calendar year: 2023 46.3% (full year), 2024 46.5% (full year), 2025 46.4% (full year), 2026 47.4% (Jan-Oct)
- Latest month Oct 2026: Actual 44.1%, Budget 43.3%
- Rolling 12-month Personnel charges / Revenue: Jan 2023 46.5% -> Oct 2026 47.3% (up 0.8 pp)

## Table

| Month | Actual | Actual R12M | Budget |
|:---|---:|---:|---:|
| Jan 2023 | 52.2% | 46.5% | 52.5% |
| Feb 2023 | 49.4% | 46.5% | 50.0% |
| Mar 2023 | 44.8% | 46.5% | 42.6% |
| Apr 2023 | 44.6% | 46.5% | 44.6% |
| May 2023 | 43.9% | 46.5% | 44.2% |
| Jun 2023 | 44.0% | 46.4% | 44.4% |
| Jul 2023 | 47.8% | 46.4% | 47.8% |
| Aug 2023 | 48.5% | 46.4% | 49.4% |
| Sep 2023 | 44.1% | 46.4% | 44.4% |
| Oct 2023 | 43.3% | 46.3% | 43.4% |
| Nov 2023 | 43.9% | 46.3% | 44.0% |
| Dec 2023 | 51.7% | 46.3% | 50.4% |
| Jan 2024 | 52.3% | 46.3% | 52.2% |
| Feb 2024 | 50.9% | 46.4% | 49.8% |
| Mar 2024 | 44.6% | 46.4% | 42.4% |
| Apr 2024 | 44.3% | 46.4% | 44.4% |
| May 2024 | 44.4% | 46.4% | 44.0% |
| Jun 2024 | 45.0% | 46.5% | 44.2% |
| Jul 2024 | 47.5% | 46.5% | 47.6% |
| Aug 2024 | 48.7% | 46.5% | 49.1% |
| Sep 2024 | 44.4% | 46.5% | 44.2% |
| Oct 2024 | 42.9% | 46.5% | 43.2% |
| Nov 2024 | 44.4% | 46.5% | 43.7% |
| Dec 2024 | 51.6% | 46.5% | 50.2% |
| Jan 2025 | 52.9% | 46.6% | 52.5% |
| Feb 2025 | 50.3% | 46.6% | 50.1% |
| Mar 2025 | 44.7% | 46.6% | 42.6% |
| Apr 2025 | 44.3% | 46.5% | 44.6% |
| May 2025 | 43.8% | 46.5% | 44.2% |
| Jun 2025 | 45.5% | 46.5% | 44.4% |
| Jul 2025 | 46.9% | 46.5% | 47.8% |
| Aug 2025 | 49.1% | 46.5% | 49.3% |
| Sep 2025 | 44.1% | 46.5% | 44.4% |
| Oct 2025 | 43.4% | 46.5% | 43.4% |
| Nov 2025 | 43.6% | 46.4% | 44.0% |
| Dec 2025 | 51.3% | 46.4% | 50.4% |
| Jan 2026 | 52.3% | 46.4% | 52.4% |
| Feb 2026 | 51.9% | 46.5% | 49.9% |
| Mar 2026 | 46.5% | 46.7% | 42.6% |
| Apr 2026 | 46.8% | 46.9% | 44.5% |
| May 2026 | 45.3% | 47.0% | 44.1% |
| Jun 2026 | 45.1% | 47.0% | 44.3% |
| Jul 2026 | 48.8% | 47.1% | 47.7% |
| Aug 2026 | 49.6% | 47.2% | 49.3% |
| Sep 2026 | 44.9% | 47.3% | 44.3% |
| Oct 2026 | 44.1% | 47.3% | 43.3% |

## Chart

`line` - Personnel charges / Revenue - Environmental Lab Testing (Jan 2023 - Oct 2026) ([interactive chart](03_show_personnel_cost_as_of_revenue_trend_for_envi_chart.html))

## Filters, version and period used

- Scope: Environmental Lab Testing
- Period: Jan 2023 - Oct 2026 (Jan 2023 - Oct 2026)
- Versions: Actual, Actual R12M, Budget
- Currency: USD at B26 (constant budget rate)
- As-of date: 2026-11-12 · row-level security: SQL Server SECURITY POLICY (SESSION_CONTEXT)

## Follow-up questions

1. Why did Personnel charges / Revenue change vs last year for Environmental Lab Testing?
2. Rank regions in Environmental Lab Testing by Personnel charges / Revenue this year
3. Compare Budget vs FC3 vs Actual for Environmental Lab Testing

## Diagnostics

```json
{
  "tool_calls": [
    {
      "name": "get_trend",
      "arguments": {
        "metric_or_ratio": "personnel_to_revenue",
        "org": "Environmental Lab Testing",
        "start": "2023-01",
        "end": "",
        "versions": [
          "Actual",
          "PY",
          "Budget"
        ]
      }
    }
  ],
  "llm_calls": [],
  "guardrail": {
    "ok": true,
    "template": true,
    "history": [
      {
        "attempt": 1,
        "ok": false,
        "unsupported": [
          "<empty>"
        ],
        "checked": 0,
        "draft": ""
      }
    ],
    "unsupported": [
      "<empty>"
    ]
  },
  "errors": [],
  "timings": {
    "preprocess": 0.008,
    "plan": 0.0,
    "act": 0.123,
    "write#1": 0.0
  }
}
```

```sql
SELECT fact_pnl.month_key, fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'Actual' AND fact_pnl.month_key BETWEEN 202202 AND 202610 AND dim_org.l4_product_line IN (N'Environmental Lab Testing') GROUP BY fact_pnl.month_key, fact_pnl.account_id
```

```sql
SELECT fact_pnl.month_key, fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'Budget' AND fact_pnl.month_key BETWEEN 202301 AND 202610 AND dim_org.l4_product_line IN (N'Environmental Lab Testing') GROUP BY fact_pnl.month_key, fact_pnl.account_id
```
