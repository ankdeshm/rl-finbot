# Compare Budget vs FC2 vs Actual for Chile Metals & Minerals

- **Persona:** Group CFO
- **Model:** `rules` · **status:** ok · **latency:** 0.11 s
- **Tool:** `compare_versions` (chosen by `router_fallback`) · **numeric guardrail:** n/a (no LLM)

## Answer

**Version comparison for Chile · Metals & Minerals, YTD Oct 2026: Actual, FC2, Budget (USD).**

- MAOP: Actual USD 705k, FC2 USD 722k, Budget USD 925k; Actual is USD 221k (23.9%) below Budget, unfavourable; FC2 is USD 204k (22.0%) below Budget, unfavourable
- Production: Actual USD 6.3M, FC2 USD 6.3M, Budget USD 6.5M; Actual is USD 134k (2.1%) below Budget, unfavourable; FC2 is USD 133k (2.1%) below Budget, unfavourable
- MAOP margin (on revenue): Actual 10.7%, FC2 11.0%, Budget 13.8%; Actual is 3.1 pp below Budget, unfavourable; FC2 is 2.8 pp below Budget, unfavourable

## Table

| Line | Actual | FC2 | Budget | Actual vs Budget | FC2 vs Budget |
|:---|---:|---:|---:|---:|---:|
| **PRODUCTION** | **6,341** | **6,342** | **6,475** | **(134)** | **(133)** |
| **REVENUE** | **6,556** | **6,558** | **6,700** | **(144)** | **(142)** |
| Personnel charges | (2,871) | (2,861) | (2,872) | 1 | 11 |
| External subcontracting | (364) | (358) | (271) | (93) | (87) |
| Other costs | (1,893) | (1,893) | (1,898) | 5 | 5 |
| Total functional costs | (668) | (667) | (666) | (2) | (1) |
| **GROSS PROFIT** | **1,373** | **1,389** | **1,591** | **(219)** | **(202)** |
| **MAOP** | **705** | **722** | **925** | **(221)** | **(204)** |
| **MANAGEMENT OP** | **639** | **655** | **851** | **(213)** | **(196)** |
| **NET INCOME** | **454** | **466** | **594** | **(140)** | **(128)** |
| MAOP margin (on revenue) | 10.7% | 11.0% | 13.8% | (3.1 pp) | (2.8 pp) |
| Gross margin | 21.6% | 21.9% | 24.6% | (2.9 pp) | (2.7 pp) |
| Direct margin | 66.0% | 66.2% | 66.7% | (0.7 pp) | (0.5 pp) |

_USD k · Signed values: costs negative. Variances are profit impact (positive = favourable)._

## Chart

`grouped_bar` - Versions - Chile · Metals & Minerals (YTD Oct 2026), costs shown as positive amounts ([interactive chart](06_compare_budget_vs_fc2_vs_actual_for_chile_metals_chart.html))

## Filters, version and period used

- Scope: Chile · Metals & Minerals
- Period: YTD Oct 2026 (Jan 2026 - Oct 2026)
- Versions: Actual (Actual, YTD Oct 2026), FC2 (FC2, YTD Oct 2026), Budget (Budget, YTD Oct 2026)
- Currency: USD at B26 (constant budget rate)
- As-of date: 2026-11-12 · row-level security: SQL Server SECURITY POLICY (SESSION_CONTEXT)

## Follow-up questions

1. Why is Actual different from Budget for Chile · Metals & Minerals this year?
2. Show the MAOP trend vs Budget for Chile · Metals & Minerals this year
3. What does the latest forecast say for the full year 2026 for Chile · Metals & Minerals?

## Diagnostics

```json
{
  "tool_calls": [
    {
      "name": "compare_versions",
      "arguments": {
        "org": "Chile \u00b7 Metals & Minerals",
        "period": "",
        "versions": [
          "Actual",
          "FC2",
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
    "preprocess": 0.009,
    "plan": 0.0,
    "act": 0.098,
    "write#1": 0.0
  }
}
```

```sql
SELECT fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'Actual' AND fact_pnl.month_key BETWEEN 202601 AND 202610 AND dim_org.l3_country IN (N'Chile') AND dim_org.l4_product_line IN (N'Metals & Minerals') GROUP BY fact_pnl.account_id
```

```sql
SELECT fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'FC2' AND fact_pnl.month_key BETWEEN 202601 AND 202610 AND dim_org.l3_country IN (N'Chile') AND dim_org.l4_product_line IN (N'Metals & Minerals') GROUP BY fact_pnl.account_id
```

```sql
SELECT fact_pnl.account_id, sum(fact_pnl.amount_usd) AS amount 
FROM fact_pnl JOIN dim_org ON fact_pnl.bu_id = dim_org.bu_id JOIN dim_version ON fact_pnl.version_id = dim_version.version_id 
WHERE dim_version.name = N'Budget' AND fact_pnl.month_key BETWEEN 202601 AND 202610 AND dim_org.l3_country IN (N'Chile') AND dim_org.l4_product_line IN (N'Metals & Minerals') GROUP BY fact_pnl.account_id
```
