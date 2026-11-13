# Evaluation report

71 golden questions (tests/golden_questions.yaml), backend `mssql`, as-of date 2026-11-12. Expected numbers are computed by raw SQL on the base tables (tests/eval_dsl.py), independently of the semantic layer. Default model: `ollama/qwen2.5-coder:14b`. All local models ran on CPU (Ollama, no GPU).

## Model comparison

| Model | Questions | Status as expected | Tool choice (final) | Tool choice (LLM alone) | Numbers in tool output | Headline number in answer text | RLS pass rate | Guardrail first pass / rewrite / redacted / template | Latency p50 / p95 (s) |
|:---|---:|---:|---:|---:|---:|---:|---:|:---|:---|
| `ollama/gpt-oss:20b` | 71 | 100% (71/71) | 100% (67/67) | 100% (67/67) | 100% (67/67) | 100% (67/67) | 100% (5/5) | 96% / 4% / 0% / 0% | 14.5 / 27.6 |
| `ollama/llama3.1:8b` | 71 | 100% (71/71) | 99% (66/67) | 97% (65/67) | 100% (67/67) | 100% (67/67) | 100% (5/5) | 79% / 19% / 1% / 0% | 12.1 / 20.5 |
| `ollama/qwen2.5-coder:14b` | 71 | 100% (71/71) | 100% (67/67) | 96% (64/67) | 100% (67/67) | 100% (67/67) | 100% (5/5) | 79% / 12% / 3% / 6% | 24.1 / 37.0 |
| `rules` (no LLM, deterministic router + templated text) | 71 | 100% (71/71) | 100% (67/67) | n/a | 100% (67/67) | 100% (67/67) | 100% (5/5) | n/a | 0.1 / 0.4 |

How to read the columns:

- **Tool choice (final)**: the tool that produced the answer is in the accepted list. When the LLM returns no usable tool call (or its call fails), a deterministic router supplies one.
- **Tool choice (LLM alone)**: the LLM's own first tool call was valid and accepted, without the router.
- **Numbers in tool output**: every expected value (SQL ground truth) is present in the table / tool output, within 1 USD or 1e-6 for ratios.
- **Headline number in answer text**: the headline value(s) appear in the written answer within display rounding (for example USD 54.4M or 17.0%).
- **Guardrail**: share of LLM answers that passed the numeric check first time, passed after one rewrite, passed after dropping the sentences with unsupported numbers, or were replaced by the templated answer.

## Per category: `ollama/gpt-oss:20b`

| Category | Questions | Status | Tool | Numbers (data) | Numbers (text) | p50 latency (s) |
|:---|---:|---:|---:|---:|---:|---:|
| pnl | 10 | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 23.5 |
| trend | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 15.4 |
| ratio | 11 | 100% (11/11) | 100% (11/11) | 100% (11/11) | 100% (11/11) | 7.0 |
| drivers | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 12.8 |
| ranking | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 12.5 |
| versions | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 16.2 |
| cockpit | 4 | 100% (4/4) | 100% (4/4) | 100% (4/4) | 100% (4/4) | 17.6 |
| followup | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 15.6 |
| rls | 5 | 100% (5/5) | 100% (3/3) | 100% (3/3) | 100% (3/3) | 12.4 |
| clarification | 2 | 100% (2/2) | n/a | n/a | n/a | 0.0 |
| robustness | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 15.8 |

Questions with at least one failed check: 0


## Per category: `ollama/llama3.1:8b`

| Category | Questions | Status | Tool | Numbers (data) | Numbers (text) | p50 latency (s) |
|:---|---:|---:|---:|---:|---:|---:|
| pnl | 10 | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 14.2 |
| trend | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 16.9 |
| ratio | 11 | 100% (11/11) | 100% (11/11) | 100% (11/11) | 100% (11/11) | 8.3 |
| drivers | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 12.2 |
| ranking | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 13.4 |
| versions | 5 | 100% (5/5) | 80% (4/5) | 100% (5/5) | 100% (5/5) | 11.3 |
| cockpit | 4 | 100% (4/4) | 100% (4/4) | 100% (4/4) | 100% (4/4) | 14.5 |
| followup | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 12.7 |
| rls | 5 | 100% (5/5) | 100% (3/3) | 100% (3/3) | 100% (3/3) | 11.7 |
| clarification | 2 | 100% (2/2) | n/a | n/a | n/a | 0.0 |
| robustness | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 10.6 |

Questions with at least one failed check: 1

| id | status | tool | data | text | note |
|:---|:---|:---|:---|:---|:---|
| ver_ca_fc3_full_year | ok (exp. ok) | get_pnl | True | True |  |

## Per category: `ollama/qwen2.5-coder:14b`

| Category | Questions | Status | Tool | Numbers (data) | Numbers (text) | p50 latency (s) |
|:---|---:|---:|---:|---:|---:|---:|
| pnl | 10 | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 30.0 |
| trend | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 31.2 |
| ratio | 11 | 100% (11/11) | 100% (11/11) | 100% (11/11) | 100% (11/11) | 16.1 |
| drivers | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 23.4 |
| ranking | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 23.1 |
| versions | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 21.5 |
| cockpit | 4 | 100% (4/4) | 100% (4/4) | 100% (4/4) | 100% (4/4) | 19.3 |
| followup | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 24.4 |
| rls | 5 | 100% (5/5) | 100% (3/3) | 100% (3/3) | 100% (3/3) | 27.3 |
| clarification | 2 | 100% (2/2) | n/a | n/a | n/a | 0.0 |
| robustness | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 25.4 |

Questions with at least one failed check: 0


## Per category: `rules`

| Category | Questions | Status | Tool | Numbers (data) | Numbers (text) | p50 latency (s) |
|:---|---:|---:|---:|---:|---:|---:|
| pnl | 10 | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 0.1 |
| trend | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 0.1 |
| ratio | 11 | 100% (11/11) | 100% (11/11) | 100% (11/11) | 100% (11/11) | 0.1 |
| drivers | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 0.1 |
| ranking | 8 | 100% (8/8) | 100% (8/8) | 100% (8/8) | 100% (8/8) | 0.3 |
| versions | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 0.1 |
| cockpit | 4 | 100% (4/4) | 100% (4/4) | 100% (4/4) | 100% (4/4) | 0.3 |
| followup | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 0.1 |
| rls | 5 | 100% (5/5) | 100% (3/3) | 100% (3/3) | 100% (3/3) | 0.1 |
| clarification | 2 | 100% (2/2) | n/a | n/a | n/a | 0.0 |
| robustness | 5 | 100% (5/5) | 100% (5/5) | 100% (5/5) | 100% (5/5) | 0.1 |

Questions with at least one failed check: 0


