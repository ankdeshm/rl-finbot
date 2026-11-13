# Moving to production

This page lists what changes when the prototype runs on the customer's SQL Server and real P&L
data. The agent, tools and UI talk only to the semantic layer, and the semantic layer reads only
SQL views. Most of the work is therefore mapping the customer's tables to those views.

## 1. Data: point the views at the real tables

1. **Keep the view contract.** Keep `v_org`, `v_account`, `v_period`, `v_version`, `v_pnl_leaf`, `v_stats`, `v_employee` and `v_employee_month` with the same column names, and redefine them in `sql/views.sql` on top of the customer's tables.
   - Typical sources are the monthly general-ledger P&L fact, the org hierarchy (org levels down to BU), the account master and the HR / timesheet extracts.
2. **Map the semantic layer.** The query builder reads `fact_pnl` / `fact_stats` / `fact_employee_month` / `dim_*` through SQLAlchemy table objects in `app/db.py`. Either:
   - expose the customer's data under those names (views or synonyms), or
   - change the table definitions in `app/db.py`.
3. **Match the chart of accounts.** Load the customer's leaf accounts into `dim_account` with their P&L line, group (direct / indirect staff costs) and sign, and use the customer's own line names as display names. Check the subtotal formulas in `metrics.yaml` against the customer's monthly P&L report.
4. **Versions and exchange rates.**
   - Map Actual / Budget / forecasts to `dim_version`.
   - If several exchange-rate bases exist (budget rate, actual rate, ...), add a rate column and a default in `settings.yaml`.
5. **Reconcile before go-live.** `make reconcile` compares semantic-layer subtotals with raw SQL. Add a comparison with the published dashboard numbers for a few BUs and months.

## 2. Security

| Item | Production setting |
|---|---|
| Database login | A dedicated SQL login or Entra ID managed identity with SELECT on the reporting views only (as `finbot_reader` in `sql/rls.sql`) |
| Row-level security | Replace `user_org_access` with the existing entitlement tables (dashboard user filters or a directory group → org-level mapping) and keep the SECURITY POLICY + `SESSION_CONTEXT` pattern |
| User identity | The UI sets `user_id` from SSO (Entra ID / Okta) instead of the persona selector |
| Secrets | Key Vault / Secret Manager; never in `.env` files on shared hosts |
| LLM data flow | The LLM receives only pre-aggregated facts (no row-level data). Use a provider and region covered by the customer's data-processing agreement, or a self-hosted model |
| Audit | Log every question, the user, the tool calls and the SQL statements (they are already returned in each answer's diagnostics) |

## 3. LLM choice

- **Changing models.** `LLM_MODEL` takes any LiteLLM model string, for example `azure/<deployment>`, `vertex_ai/gemini-2.5-flash`, `bedrock/...` or `ollama/...`.
- **Choosing a model.** Re-run `make eval` with each candidate. The report compares tool choice, numeric accuracy, guardrail outcomes and latency on the same questions.
- **CPU-only models.** These run at 20–100 s per answer in this prototype (see the eval report). Production needs a GPU-backed endpoint or a managed API for interactive use.

## 4. Hosting

| Option | Notes |
|---|---|
| Container (Dockerfile) | Azure Container Apps / App Service, AKS, Cloud Run or on-prem Docker. ODBC Driver 18 is in the image |
| docker compose | Single VM next to SQL Server; ports bound to localhost behind a reverse proxy with SSO |
| Kubernetes | As in this prototype (`deploy/k8s/`); expose through an ingress with SSO instead of port-forward |

## 5. Relationship to Tableau

- **Tableau stays the system for standard dashboards.** The copilot covers the ad-hoc questions that today become dashboard requests.
- **Same numbers.** Both read the same SQL Server views, so the figures match. A Tableau extract of the views can be reconciled automatically.
- **Linking out.** Answers can link to the matching Tableau view by passing the resolved filters (org, period, version) as URL parameters.

## 6. Checklist

- [ ] Views mapped to the customer's tables; `make reconcile` shows 0 mismatches against the published P&L.
- [ ] Entitlements mapped; RLS tests pass for real users.
- [ ] Golden questions rewritten with the customer's names; `make eval` meets the agreed thresholds.
- [ ] LLM endpoint approved by security; prompts contain no row-level data.
- [ ] SSO in front of the UI; audit log enabled.
