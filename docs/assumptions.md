# Assumptions

The prototype runs on synthetic data for a fictional company. It mirrors the structures in the
customer's material: the AD50 monthly report and the "Performance Cockpit" Tableau screens. The
choices below were made where the material was silent. Each one can be changed in
`config/settings.yaml`, `app/semantic/metrics.yaml` or `scripts/generate_data.py`.

## Company and scope

| Topic | Assumption |
|---|---|
| Company | "RL Certification & Inspection" (RL Group), a fictional TIC company that competes with SGS, Bureau Veritas, Intertek and Dekra |
| Geography | Americas only: 5 regions (US & Canada, Mexico, Northern South America, Southern South America, BPU = Brazil / Paraguay / Uruguay), 11 countries |
| Sectors (product lines) | Buildings & Infrastructure, Industry & Energy, Power & Utilities, Elevators & Pressure Vessels, Environmental Lab Testing, Consumer Products, Certification & Sustainability, Metals & Minerals |
| Hierarchy | group > region > country > sector > business (sector + city) > BU; 109 BUs |
| Time | Jan 2022 – Dec 2026, monthly; as-of date 2026-11-12; a month closes on the 5th of the next month |

## Financial structure

| Topic | Assumption |
|---|---|
| P&L layout | The AD50 monthly report from the Tableau screenshot replaces the generic 14-line P&L of the first specification. The subtotals follow the screenshot: Revenue = 1+2, Production = 3+4+5, Gross profit = 6..10, MAOP = 11+12, Management OP = 13+17, Net income = 18+19+20 |
| "Operating result" (first specification) | Mapped to line 11 Gross profit (production minus direct costs, before functional costs); MAOP = line 13 |
| Personnel 7A / 7B | 7A = production (direct) employees, 7B = non-production employees, with leaf accounts for salary, bonus, variable/overtime, social security, pension and other |
| Functional neutralization (10) | A small positive line (about 2.5% of the BU's production trend) that offsets functional charges booked in other costs |
| Functional costs (12) | Country, region and HQ allocations; HQ allocation is spread evenly over the months of a year |
| Taxes (20) | Country tax rate × pre-tax result, per BU and month |
| Financial result (19) | Net interest plus an FX result that depends on country volatility (zero for USD; Argentina has a negative drift) |
| Currency | USD at budget rate B26 (constant currency), as in the Tableau filters "Currency USD / Rate code B26" |
| Versions | Actual, Budget, FC1 (4 actual + 8 forecast months), FC2 (8 + 4), FC3 (9 + 3). Later forecasts sit closer to the outcome (accuracy 0.45 / 0.70 / 0.85) |
| Budget | Prior-year actual × target growth, with a slight optimism bias |

## Operational KPIs (cockpit)

The definitions follow the "Operational Profitability – Direct Margin Drivers" screen:

| KPI | Definition |
|---|---|
| Direct margin | (production + 7A direct labor) / production, with 7A signed negative; a variant including external subcontracting is also available |
| Utilization rate | billable hours / available hours of direct staff |
| Production per hour | production / billable hours |
| Production per FTE | production × 12 / sum of monthly FTE (annualised) |
| Overtime ratio | overtime hours / available hours |
| Production hourly cost | 7A direct labor / billable hours |
| Direct labor cost over production | 7A / production |

Available hours assume 150 hours per direct FTE per month before seasonality.

## Data generation

| Topic | Assumption |
|---|---|
| Cost profiles | By business type, as a share of production: inspection is personnel-heavy (about 60%), infrastructure subcontracting-heavy (about 18%), laboratories have high other costs (consumables, depreciation), certification has the highest margin |
| Seasonality | Northern countries: March peak, August and December dips. South America: January/February summer dip, July winter break, December dip |
| Stories | Five planted business stories (see `docs/demo_stories.md`) |
| Reproducibility | Fixed seed `20261112`; `make data` always produces the same tables |

## Personas and access

| Persona | Scope |
|---|---|
| Group CFO | whole group |
| United States Country Head | United States only |
| Environmental Lab Testing PL Leader | Environmental Lab Testing in every country |

A question outside a persona's scope is refused without data. A question wider than the scope
(for example "the whole group" from the US country head) is answered for the allowed part, and
the answer says so.

## Not covered by the prototype

- Balance sheet, cash flow and order intake / backlog.
- Intercompany eliminations beyond lines 4 and 5.
- Local-currency reporting, or more than one FX rate code.
- The customer's real data. When it becomes available, the generator is replaced by a load from the existing SQL Server tables (see `docs/production_migration.md`).
