# Earlier evaluation runs

These runs are kept so the fixes in [APPENDIX.md](../../../APPENDIX.md) (section 3) can be checked against raw answers. Each run uses the same 71 questions, models and hardware as the final results in [`results/eval/`](../); only the agent code differs.

| File | Agent code |
|---|---|
| `qwen2.5-coder-14b_initial_code.jsonl` | Before the answer fixes: P&L bullets used fixed lines, `get_pnl` followed an Actual-only request, the guardrail could drop the headline sentence, and account questions had no account fact |
| `qwen2.5-coder-14b_intermediate_code.jsonl` | Has those fixes, but account answers still include the MAOP explanation, and the last fix round is missing (see next row) |
| `llama3.1-8b_intermediate_code.jsonl`, `gpt-oss-20b_intermediate_code.jsonl` | All fixes except the last round: Actual as the main version for "vs budget" questions, headline figure first in driver answers and in P&L answers with no named line, and pure follow-ups keeping the previous tool |

The final runs in `results/eval/*.jsonl` use the final code.
