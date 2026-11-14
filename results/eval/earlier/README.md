# Earlier evaluation run

This run is kept so the narrative checks in [APPENDIX.md](../../../APPENDIX.md) (section 3) can be compared
with raw answers. It uses the same 82 questions, data, models and hardware as the final results in
[`results/eval/`](../); only the agent code differs.

| File | Agent code |
|---|---|
| `*_before_narrative_checks.jsonl` | Before the narrative checks: numbers were checked for existence only (not for their month, leaver type or scope), causes were not checked, leaver facts had no per-type change, "highest first" breakdowns listed zero values, and customer terms from the question were repeated in answers |
| `summary_before_narrative_checks.json` | Summary of those runs, in the same format as `results/eval/summary.json` |

The final runs in `results/eval/*.jsonl` use the final code.
