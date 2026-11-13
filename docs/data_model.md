# Data model

A star schema in SQL Server 2022 (`sql/schema.sql`). A DuckDB copy with the same tables and
views (`scripts/export_duckdb.py`) supports a laptop or Hugging Face demo. The data is synthetic
and seeded (`config/settings.yaml`), so every run produces the same numbers.

## Storage rules

- **Signed amounts.** Revenue is positive and cost is negative, in USD at budget rate B26.
- **Leaf accounts only.** Fact rows exist only for leaf accounts. Every line, subtotal and ratio is computed from leaves at query time.
- **Versions in one fact table.** Actual, Budget, FC1, FC2 and FC3 sit in the same table. PY (prior year) is not stored: it is Actual shifted back 12 months.
- **Forecasts.** FCn holds actuals for the first months of the year and a reforecast for the rest. FC1 = 4 + 8, FC2 = 8 + 4, FC3 = 9 + 3. A forecast becomes available after the close of its last actual month, which is the 5th of the following month.
- **Last closed month.** With the as-of date 2026-11-12, the last closed month is October 2026. Actuals stop there.

## Tables

| Table | Rows | Content |
|---|---:|---|
| `dim_org` | 109 | Org hierarchy: L1 group > L2 region > L3 country > L4 product line (sector) > L5 business (sector + city) > L6 BU (e.g. `US-EPV-DEN-01`), plus business type, city and SCD2 validity columns |
| `dim_account` | 57 | AD50 chart of accounts: line number, line name, group code (7A/7B), leaf code (e.g. 7A2, 9.3), leaf/subtotal flags, natural sign, favourable direction, display order |
| `dim_version` | 5 | Actual, Budget, FC1, FC2, FC3, with the number of actual months in each forecast |
| `dim_period` | 60 | Jan 2022 – Dec 2026: year, quarter, month, close date, closed flag |
| `fact_pnl` | 1,201,834 | month × BU × leaf account × version → `amount_usd` (DECIMAL(18,2), signed) |
| `fact_stats` | 32,482 | month × BU × version → FTE, headcount, direct FTE, billable / available / overtime hours |
| `app_user` | 3 | Demo personas |
| `user_org_access` | 3 | Org-level grants per persona (row-level security) |

`fact_pnl` rows per version: Actual 233,914 (58 closed months); Budget, FC1, FC2 and FC3 241,980 each (60 months).

## AD50 management P&L lines

| Line | Name | Definition |
|---:|---|---|
| 1 | Billing | leaves 1.1 external billing, 1.2 credit notes |
| 2 | WIP & UI | leaves 2.1 change in WIP, 2.2 change in unearned income |
| **3** | **REVENUE** | 1 + 2 |
| 4 | Intragroup revenue | leaf |
| 5 | Intragroup subcontracting | leaf (cost) |
| **6** | **PRODUCTION** | 3 + 4 + 5 (production is not revenue) |
| 7 | Personnel charges | 7A direct labor (7A1 guaranteed salary, 7A2 bonus, 7A3 variable/overtime, 7A4 social security, 7A5 pension, 7A6 other) and 7B indirect |
| 8 | External subcontracting | 8.1 external subcontractors, 8.2 temporary staff |
| 9 | Other costs | 9.1 contract expenses … 9.9 (rent, depreciation, travel, vehicles, IT, lab consumables, insurance, other) |
| 10 | Functional neutralization | leaf |
| **11** | **GROSS PROFIT** | 6 + 7 + 8 + 9 + 10 |
| 12 | Total functional costs | 12.1 country, 12.2 region, 12.3 HQ allocation |
| **13** | **MAOP** (management AOP) | 11 + 12 |
| 17 | Other operating expenses | 17.1 restructuring, 17.2 PPA amortisation |
| **18** | **MANAGEMENT OP** | 13 + 17 |
| 19 | Financial result | 19.1 net interest, 19.2 FX result |
| 20 | Corporate taxes | leaf |
| **21** | **NET INCOME** | 18 + 19 + 20 |

Lines 14–16 are not used, to keep the AD50 numbering. The subtotal structure was checked against the numbers in the AD50 Tableau screenshot.

## Statistics and KPIs

- **Stocks** (FTE, headcount, direct FTE) are averaged over the months of the period and summed over BUs.
- **Flows** (billable, available and overtime hours) are summed.
- **KPI cockpit** ("Operational Profitability – Direct Margin Drivers"):
  - direct margin = (production + 7A) / production
  - production
  - direct labor cost (7A)
  - utilization rate = billable / available hours
  - production per billable hour
  - production per FTE (annualised)
  - overtime ratio
  - production hourly cost
  - direct labor / production
  - gross margin
  - MAOP margin

  Every KPI is shown MTD and YTD, vs LY and vs Budget.

## Views

`sql/views.sql` defines the reporting views: `v_org`, `v_account`, `v_period`, `v_version`,
`v_pnl_leaf` and `v_pnl` (leaf rows plus AD50 subtotal membership), and `v_stats`.

- The agent's fallback tool `run_readonly_sql` may only read these views.
- The same views are replayed on DuckDB.

## Row-level security

Row-level security is enforced in two places:

- **SQL Server.**
  - `sql/rls.sql` creates `rls.fn_org_access` and a SECURITY POLICY on `fact_pnl` and `fact_stats`.
  - Rows are filtered by `SESSION_CONTEXT('user_id')`, which the app sets read-only on every connection.
  - The app connects as the least-privilege login `finbot_reader`, which has SELECT only. The admin login is used only by the loader.
- **Semantic layer.**
  - Applies the same rules before querying (`app/semantic/access.py`), so it can explain a refusal or a narrowed scope politely.
  - On DuckDB this is the only enforcement.

| Persona | `user_id` | Access |
|---|---|---|
| Group CFO | `group_cfo` | whole group |
| United States Country Head | `us_country_head` | `l3_country = United States` |
| Environmental Lab Testing PL Leader | `env_pl_leader` | `l4_product_line = Environmental Lab Testing` |
