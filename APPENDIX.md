# Appendix

Detailed progression, what worked and what did not, and extended caveats. The short version is
in [README.md](README.md); raw outputs are in [`results/`](results/).

## 1. Environment and constraints

| Constraint | What happened | Resolution |
|---|---|---|
| Corporate laptop (Santa) | Docker, Colima, the uv-managed Python 3.11, Ollama (banned by TeamID) and cloudflared (banned as a reverse proxy) are blocked | Everything runs on an existing GKE CPU node pool (2× c3-standard-44). Only `kubectl` runs on the laptop |
| Shared CPU nodes | Other services *reserve* about 96% of each node's CPU but use almost none of it | Pods request little (≈1 vCPU in total) with high limits, so they use idle capacity and yield under contention. Existing services were not touched |
| Public URL (`make tunnel`) | cloudflared is banned; a public tunnel from a corporate project would bypass security controls | `make tunnel` is implemented for non-corporate environments but was not run. The UI is reached with `make k8s-forward` (authenticated port-forward) |
| Docker validation | No Docker daemon available | The Dockerfile was built in-cluster with kaniko (`--no-push`) in about 63 s; log in `results/build/` |
| Vertex AI Gemini comparison | (1) Project IAM change denied for the user account. (2) The user's OAuth token type is rejected by Vertex AI (`ACCESS_TOKEN_TYPE_UNSUPPORTED`). (3) The pod's Workload Identity reaches Vertex but lacks `aiplatform.endpoints.predict` | Not run. One IAM binding (`roles/aiplatform.user` for the dev service account) enables it; the code path is in place (`LLM_MODEL=vertex_ai/gemini-2.5-flash`) |
| GitHub | No token on the laptop, and its SSH key is not registered with GitHub (`Permission denied (publickey)`) | Local git repo + `scripts/publish_github.sh` (`GITHUB_TOKEN=... ./scripts/publish_github.sh`) |

## 2. Progression

1. **First version: "XYZ Group", Europe, EUR.** Data, SQL Server load, DuckDB export and reconciliation passed: 101 BUs, 933k fact rows, 0 mismatches over 200 subtotal checks. It was superseded by the re-theme below.
2. **Re-theme to RL Certification & Inspection (Americas, USD).**
   - The P&L was rebuilt with the line structure of a typical TIC monthly management report (revenue, production, personnel, subcontracting, other and functional costs, operating profit, EBIT, net income).
   - The org became 5 regions and 11 countries, with 8 sectors.
   - Operational KPIs (direct margin, utilization, production per hour / FTE, overtime ratio, production hourly cost) were added as statistics, ratios and the `get_kpi_cockpit` tool.
3. **Data, semantic layer, agent, UI, evaluation and packaging** (first full version): 109 BUs, 1,201,834 P&L fact rows, 71 golden questions, rules and three local LLMs evaluated. Those results are kept in `results/eval/earlier/*_previous_dataset.jsonl`.
4. **Generic labels, Environmental Lab Testing scope, employee records** (current version):
   - All labels are generic: "Operating profit" and "EBIT" instead of customer-specific line names, "general ledger (GL) P&L" instead of a report name, "constant budget rate" instead of a rate code, no account codes or line numbers in labels, no real place or person names. Customer terms still work in questions as synonyms.
   - KPI levels were moved away from any real dashboard values (utilization about 74%, overtime about 6%).
   - Environmental Lab Testing exists only in Canada (5 BUs) plus one small US unit; the lost-contract story moved to Canada Environmental Lab Testing.
   - New fictional employee records (27,360 employees, 937,506 employee-months) that add up exactly to the BU statistics, a `get_workforce` tool, 11 workforce golden questions (82 in total) and 4 workforce example buttons.
   - The data now has 106 BUs, 1,168,756 P&L fact rows and 31,588 statistics rows; SQL Server load 33.9 s; 0 mismatches over 300 subtotal checks.

## 3. What did not work at first, and the fix

| Symptom | Cause | Fix |
|---|---|---|
| The LLM wrote "production outperformed budget" when production was 1.9% below budget, and called cost increases "neutral" | Small CPU models infer directions badly from raw numbers | Facts spell out every comparison ("USD 6.3M (1.9%) below Budget (USD 328.8M), unfavourable") and the main reasons ("Operating profit vs PY: increase of USD 3.5M driven by …, partly offset by …"). The LLM writes only 2–4 sentences; key-figure bullets are added deterministically |
| Bridge items labelled "neutral" | `numpy.bool_` is not `True`, so favourability text fell through to "neutral" | `_fav_word` accepts any truthy value and treats NaN as neutral |
| Planner step 26–31 s per question | Ollama with one slot re-processed the 2.7k-token planner prompt after every writer call | `OLLAMA_NUM_PARALLEL=2`: planner and writer keep their own KV cache; the planner step dropped to about 9 s |
| qwen2.5-coder returns tool calls as JSON text, not native calls | Model / template behaviour in Ollama | The text tool-call parser recovers them; the source is recorded per answer (`llm_text`) |
| qwen never chose the new workforce tool by itself | The text tool-call parser had its own hard-coded list of tool names, without the new tool, so its calls were dropped and the router answered | The parser list now includes the tool, and a test checks that it covers every tool |
| "why is the first one so low?" answered for the whole group | Follow-ups did not remember ranked entities | Memory stores the ranked / drilled entities; ordinal references resolve to them |
| "H1 2026" lost after routing | The router passed "2026-01 to 2026-06", which the parser read as January | Explicit month-range patterns (ISO and month names) |
| "Mexcio" not recognised | The similarity cutoff (86) missed a transposition (83) | One adjacent-letter swap is accepted; substitutions stay strict so "lower" never becomes "power" |
| "latest forecast for the full year" returned YTD numbers | Comparisons were truncated like-for-like to the last Actual month | Full-year version view: Budget and forecasts for Jan–Dec, Actual left out with a note |
| Bonus / restructuring questions answered with the line-level P&L | Leaf metrics were routed to `get_pnl` | Leaf and group metrics route to `variance_drivers` (total vs PY, account and org drill-down) |
| "Split personnel into direct and indirect" showed leaf accounts only | Depth-2 breakdown skipped the direct / indirect staff level | Breakdowns also return sub-group totals |
| Trend facts averaged monthly percentages | Yearly values were the mean of monthly ratios | Yearly ratio = sum(numerator) / sum(denominator) over the months shown |
| Schema test failed on SQL Server syntax | sqlglot cannot parse `SELECT @sql += …` | The test parses only the CREATE TABLE statements |
| UI deprecation warnings | `use_container_width` is deprecated in Streamlit 1.67 | `width="stretch"` |
| Operating profit bridge steps barely visible | The waterfall axis started at zero, with totals of about USD 50M and steps of a few USD M | The value axis zooms when every running level is positive and the lowest is at least 35% of the highest (`tests/test_charts.py`) |
| qwen's answer to "What is the net income of Mexico this year?" never stated net income | The P&L key-figure bullets always used the same lines (production, personnel, gross profit), and the guardrail had dropped the narrative sentence that held the figure | The line the question asks about is always the first bullet |
| The same answer said "lower net income" with nothing to compare against | The LLM planner asked `get_pnl` for Actual only, and the tool followed it | Unless the user names versions or comparisons, `get_pnl` always adds PY and Budget, as the rules router does |
| Some redacted answers opened with "This improvement is driven by …" | The guardrail had dropped the first sentence (the headline), so the rest pointed back to a sentence that was gone and could keep unsupported causes | If the headline sentence has to be dropped, the templated answer is used instead |
| On the previous dataset, qwen called the operating profit (USD 919k) "restructuring costs" for the lab business with the lost contract; the real figure was USD 960k | The LLM picked `get_pnl`. The restructuring account was in the table but not in the facts, so the model reused a nearby number, and the guardrail passed it because USD 919k exists in the output | When the question names an account or sub-group, `get_pnl` includes it (deeper account level if needed) and states it as the first fact and bullet. The operating-profit variance explanation is left out of such answers: with it in the facts, qwen stated USD 960k but wrote that the increase was "driven by Production (USD 5.4M lower)" |
| llama answered "How is Colombia doing vs budget?" with Budget figures presented as results ("all above budget") | The planner asked `get_pnl` for Budget only, so Budget became the main version | For a comparison question ("vs", "against", "compared") on a closed period, Actual is always the main version |
| llama's answers to "Why is subcontracting above budget?" and "How is the whole group doing vs budget?" gave the gaps but not the amounts | Driver bullets started with the accounts, and P&L bullets without a named line skipped the headline profit line | Driver bullets start with the total and its change; P&L bullets start with operating profit when no line is named |
| llama answered "now for Canada" (after a P&L question) with the KPI cockpit | The follow-up changed only the scope, but the LLM picked a different tool | A pure follow-up keeps the previous turn's tool. The eval counts this as a router decision, not the LLM's |
| The numeric guardrail ignored counts followed by a word ("62 restructuring", "353 employees") | The check for codes such as "7A1" looked at the first letter after the number *and the following space*, so any number followed by a word was skipped | Only a letter directly after the digits marks a code; counts followed by a word are now checked |
| A restructuring month showed 190% attrition in the monthly view | A single month annualised (leavers × 12 / headcount) exaggerates one-off exits | Monthly rows show attrition over the rolling 12 months to that month; period totals stay annualised over the period |
| "Turnover" questions could mean revenue or attrition | Finance teams use "turnover" for revenue | "Turnover" alone stays revenue; "staff turnover" or "turnover rate" goes to the workforce tool |

## 4. Evaluation details

- **Expected values.** `tests/eval_dsl.py` compiles small specs (measure, org, period, version, ranking, workforce figure) straight to SQL on the base tables. It does not use the semantic layer, the views or the metric registry.
- **Checks per question:** status (ok / refusal / clarification), primary tool, every expected value in the tool output, headline value(s) in the answer text, RLS behaviour, guardrail outcome, latency.
- **Golden set.** 82 questions: P&L, trends, ratios, drivers, rankings, versions, KPI cockpit, follow-ups, row-level security, clarification, robustness (typos, leaf accounts, three questions that use customer terms as synonyms) and 11 workforce questions.
- **Rules baseline.** The deterministic router without an LLM scored 57/71 on its first run; after the fixes above it passes every check. The golden set and the router were developed together, so the rules score shows what the semantic layer supports. It is not a generalisation measure.
- **LLM fixes came from the same questions.** The LLM-side fixes in section 3 were found by reading failed answers on this golden set, so the LLM scores are not held-out either. The fixes are general rules (state the figure that was asked for, Actual as the main version, keep the tool on a pure follow-up), not per-question patches. Earlier runs are kept in `results/eval/earlier/`.
- **LLM runs.** Each LLM run answers the same questions; multi-turn questions replay their earlier turns. All local models ran on CPU through Ollama 0.40.16.

The full per-model results are in [eval_report.md](eval_report.md) and `results/eval/*.jsonl`.

## 5. Caveats

- **Synthetic data.** All companies, people, figures and stories are invented; see `docs/assumptions.md`.
- **CPU latency.** Local LLMs ran on a shared CPU node, with no GPU. Interactive production use needs a GPU-backed or managed model endpoint.
- **Guardrail scope.** The guardrail checks that every number exists in the tool output. It does not check what the number is attached to, or causes stated without numbers.
  - On the previous dataset, qwen once called the operating profit "restructuring costs" and the check passed (fixed, see section 3).
  - LLM text can still add causes that are not in the data. Directions are protected by the explicit comparison facts and the deterministic bullets. The table and the bullets always come straight from the data; the narrative should be read as a summary of them.
- **Workforce data.** Employee records exist for closed months only and have no budget, so workforce answers compare with the prior year only.
- **Personas.** Three personas demonstrate row-level security; production would map real entitlements (see `docs/production_migration.md`).
