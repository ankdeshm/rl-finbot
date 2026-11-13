# why is the first one so low?

- **Persona:** Group CFO
- **Model:** `rules` · **status:** ok · **latency:** 0.18 s
- **Tool:** `variance_drivers` (chosen by `router_fallback`) · **numeric guardrail:** n/a (no LLM)

## Answer

**MAOP margin (on revenue) for Ecuador, YTD Oct 2026: Actual 9.4%, 1.7 pp below PY (11.1%), unfavourable.**

Account drivers (largest first): Personnel charges as % of revenue: 51.0% vs 50.1%, impact on MAOP margin (on revenue) -0.9 pp (unfavourable); External subcontracting as % of revenue: 18.7% vs 18.1%, impact on MAOP margin (on revenue) -0.6 pp (unfavourable); Total functional costs as % of revenue: 10.5% vs 10.2%, impact on MAOP margin (on revenue) -0.2 pp (unfavourable); Other costs as % of revenue: 12.2% vs 12.1%, impact on MAOP margin (on revenue) -0.1 pp (unfavourable); Functional neutralization as % of revenue: 2.5% vs 2.4%, impact on MAOP margin (on revenue) +0.1 pp (favourable).

- Product line with the largest change: Buildings & Infrastructure 9.5% vs 12.0% (-2.5 pp, unfavourable)

## Table

| Driver | PY | Actual | Impact | Share of variance |
|:---|---:|---:|---:|---:|
| Personnel charges as % of revenue | 50.1% | 51.0% | (0.9 pp) | 53.2% |
| External subcontracting as % of revenue | 18.1% | 18.7% | (0.6 pp) | 36.0% |
| Total functional costs as % of revenue | 10.2% | 10.5% | (0.2 pp) | 13.9% |
| Other costs as % of revenue | 12.1% | 12.2% | (0.1 pp) | 5.6% |
| Functional neutralization as % of revenue | 2.4% | 2.5% | 0.1 pp | (4.8%) |
| Production as % of revenue | 99.2% | 99.3% | 0.1 pp | (3.9%) |

_Impact = contribution to the change in MAOP margin (on revenue) (percentage points)_

**By product line**

| Product line | PY | Actual | Impact |
|:---|---:|---:|---:|
| Buildings & Infrastructure | 12.0% | 9.5% | (2.5 pp) |
| Industry & Energy | 8.5% | 9.1% | 0.6 pp |

## Chart

`waterfall` - MAOP margin (on revenue): PY to Actual - Ecuador (YTD Oct 2026) ([interactive chart](14_why_is_the_first_one_so_low_chart.html))

## Filters, version and period used

- Scope: Ecuador
- Period: YTD Oct 2026 (Jan 2026 - Oct 2026)
- Versions: Actual (Actual, YTD Oct 2026), PY (Actual, YTD Oct 2025)
- Currency: USD at B26 (constant budget rate)
- As-of date: 2026-11-12 · row-level security: SQL Server SECURITY POLICY (SESSION_CONTEXT)

## Follow-up questions

1. Show the monthly trend of MAOP margin (on revenue) for Ecuador since 2025
2. Show the Personnel charges trend for Ecuador vs budget
3. Compare Budget vs FC3 vs Actual for Ecuador

## Diagnostics

```json
{
  "tool_calls": [
    {
      "name": "variance_drivers",
      "arguments": {
        "metric": "maop_margin_revenue",
        "org": "Ecuador",
        "period": "YTD Oct 2026",
        "comparison": "PY",
        "depth": 1
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
    "preprocess": 0.009,
    "plan": 0.0,
    "act": 0.164,
    "write#1": 0.0
  }
}
```

```sql
SELECT fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'Actual' AND fact_pnl.month_key BETWEEN 202601 AND 202610 AND dim_org.l3_country IN (N'Ecuador') GROUP BY fact_pnl.account_id
```

```sql
SELECT fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'Actual' AND fact_pnl.month_key BETWEEN 202501 AND 202510 AND dim_org.l3_country IN (N'Ecuador') GROUP BY fact_pnl.account_id
```

```sql
SELECT dim_org.l4_product_line, fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'Actual' AND fact_pnl.month_key BETWEEN 202601 AND 202610 AND dim_org.l3_country IN (N'Ecuador') GROUP BY dim_org.l4_product_line, fact_pnl.account_id
```

_1 more SQL statements in the JSON file._
