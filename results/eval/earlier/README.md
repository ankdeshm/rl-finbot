# Earlier evaluation runs

These runs are kept so the changes described in [APPENDIX.md](../../../APPENDIX.md) can be compared with raw
answers. They use the same data, models and hardware as the final results in [`results/eval/`](../); only the
agent code (and, for the first set, the number of questions) differs.

| File | Questions | Agent code |
|---|---|---|
| `*_before_narrative_checks.jsonl` | the 82 questions before the test conversations were added | Before the narrative checks: numbers were checked for existence only (not for their month, leaver type or scope), causes were not checked, leaver facts had no per-type change, "highest first" breakdowns listed zero values, and customer terms from the question were repeated in answers |
| `summary_before_narrative_checks.json` | same | Summary of those runs, in the same format as `results/eval/summary.json` |
| `rules_before_conversation_fixes.jsonl` | the 12 test conversations only (category `conversation`), rules mode | Before the conversation fixes: negations were ignored, "compare with last year" changed the period, follow-ups lost the P&L line asked about, only short or "now / and / what about" questions counted as follow-ups, and pushback re-ran the question |

The final runs in `results/eval/*.jsonl` use the final code.
