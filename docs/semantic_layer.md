# Semantic layer

The semantic layer is the only path from a question to a number. The LLM never writes the SQL
for standard questions and never does arithmetic. Every figure comes from
`app/semantic/query_builder.py`.

## Definitions: `app/semantic/metrics.yaml`

| Section | Content |
|---|---|
| `lines` | AD50 lines 1–21 with id, name, natural sign (+1 revenue / −1 cost), favourable direction, subtotal formula and synonyms (for example "MOP", "operating profit" → MAOP; "staff cost", "payroll" → personnel charges) |
| `groups` | 7A direct labor cost and 7B indirect personnel cost |
| `computed` | direct margin amount = production + 7A; direct margin incl. subcontracting = production + 7A + 8 |
| `leaf_synonyms` | business words for leaf accounts ("bonus" → 7A2, "temps" → 8.2, "lab consumables" → 9.7, "restructuring" → 17.1) |
| `stats` | FTE, headcount, direct FTE (averaged over months) and billable / available / overtime hours (summed) |
| `ratios` | 21 ratios with format (percent or currency) and favourable direction: margins (direct, gross, MAOP on revenue / production, management OP, net income), cost ratios (personnel / billing / revenue / production, 7A / production, subcontracting %, other cost %, functional cost %), productivity (utilization, production per hour, per FTE annualised, personnel cost per FTE, production hourly cost, overtime ratio), WIP % of revenue |
| `cockpit` | the 11 KPIs of the operational profitability cockpit |
| `drivers` | the decomposition tree used by `variance_drivers` (for example MAOP = production + personnel + subcontracting + other costs + functional neutralization + functional costs) |

### Adding a metric or ratio

To add a metric or ratio, add one YAML entry. No code changes are needed:

```yaml
ratios:
  subcontracting_to_personnel:
    {name: Subcontracting / Personnel, num: subcontracting, den: personnel, format: pct, favorable: down,
     synonyms: [subcontracting to personnel, subcontracting vs staff cost]}
```

Users can also compose ratios on the fly. "A as % of B", "A / B", "A per FTE" and "A to B ratio" resolve to a known ratio, or to an ad-hoc `ratio:A/B` with the right format and direction.

## Computation

1. **Leaf query.** `fetch_leaf` and `fetch_stats` run one SQLAlchemy Core statement per version.
   - The statement covers the needed months and the org filter (plus the row-level-security filter in DuckDB mode).
   - It groups by account and any requested org level or month.
   - The compiled SQL of every statement is returned with the answer ("How I got this").
2. **Wide frame.** Leaves are pivoted to columns, then lines, groups, subtotals and computed amounts are added. The subtotals follow the AD50 formulas, applied recursively.
3. **Display values.** For single metrics, value = signed × natural sign, so a cost shows as a positive amount. The P&L statement view keeps signed values, with costs shown in parentheses.
4. **Ratios.** A ratio is always sum(numerator) / sum(denominator) over the period. It is never an average of monthly ratios. Per-FTE ratios are annualised: numerator × 12 / sum of monthly FTE.
5. **Variances.**
   - Actual − comparison, with % vs |comparison|.
   - Favourability comes from the metric's direction: costs going up are unfavourable.
   - P&L variances are profit impact.
   - Margin bridges are exact in percentage points: each driver's share of the denominator, current minus comparison.

## Time intelligence: `app/semantic/time_intel.py`

| Feature | Rule |
|---|---|
| Periods | month, QTD, YTD, R12M, FY, quarter, half-year, explicit ranges ("Jan 2026 – Jun 2026", "since 2023") |
| Last closed month | a month closes on the 5th of the following month; as-of 2026-11-12 → October 2026 |
| Like-for-like | a period that runs past the last closed month is truncated for Actual, and every comparison uses the same months (with a note) |
| PY / LY | Actual of the same months one year earlier |
| Forecasts | FC1/FC2/FC3 exist only after their cut-off has closed for that year; "latest forecast" picks the newest available |
| Full-year view | full-year version comparisons show Budget and forecasts for Jan–Dec. Actual is left out because it is incomplete, and a note says so |

## Entity resolution: `app/semantic/entity_resolver.py`

- **Org units at any level**: names, aliases ("Andean region", "southern cone", "BPU"), ISO codes in upper case, BU codes, city + sector ("Env Lab Sao Paulo"), and multi-region phrases ("South America", "LatAm").
- **Typos**: a single typo in a country, region or sector name is accepted ("Brazl", "Mexcio"). Common English words stay excluded.
- **"PY" means prior year**, never Paraguay.
- **Ambiguous cities**: a bare city with several businesses produces a clarification question.
- **Hints**: intents, top-N and ranking level are passed to the planner as RESOLVED hints. The same hints drive the fallback router.

## Guarantees checked by tests

The checks below are in `tests/test_semantic.py`, `tests/test_guardrails.py`, `tests/test_agent_rules.py` and `tests/test_ui.py`:

- Subtotals equal raw-SQL leaf sums for several orgs, versions and periods.
- Sign conventions, favourability rules and P&L variances as profit impact.
- Calendar, period parsing, latest-forecast rule and like-for-like truncation.
- Org, metric and ratio resolution, including typos and the PY / Paraguay conflict.
- Row-level security, both in the semantic layer and natively in SQL Server.
- The SQL guard: DML / DDL / EXEC / non-whitelisted tables are rejected, and the row limit is enforced.
- The numeric guardrail.
- The output contract.
- The UI renders text, table, chart and follow-ups.
