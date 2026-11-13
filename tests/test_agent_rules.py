"""End-to-end agent tests without an LLM (deterministic router + templated text). They exercise the
full LangGraph pipeline, output contract, chart selection, follow-ups, memory and refusals."""
from __future__ import annotations

from datetime import date

import pytest

from app.agent.graph import ask

AS_OF = date(2026, 11, 12)
EXAMPLES = [
    ("How is MAOP YTD vs last year and budget for the United States?", "get_pnl", "waterfall"),
    ("Show personnel cost as % of revenue trend for Environmental Lab Testing since 2023", "get_trend", "line"),
    ("Why did Brazil Environmental Lab Testing margin drop in 2026?", "variance_drivers", "waterfall"),
    ("Top 5 BUs by MAOP margin in US & Canada this year", "rank_entities", "hbar"),
    ("Compare Budget vs FC2 vs Actual for Chile Metals & Minerals", "compare_versions", "grouped_bar"),
    ("Break down 7A personnel cost for US Elevators & Pressure Vessels in March 2025", "variance_drivers", "stacked_bar"),
    ("What happened to WIP in Mexico Buildings & Infrastructure this year?", "get_trend", "line"),
    ("Subcontracting cost by product line YTD vs PY", "rank_entities", "hbar"),
    ("Show the operational profitability cockpit for Canada", "get_kpi_cockpit", "combo"),
]


@pytest.mark.parametrize("q,tool,chart", EXAMPLES)
def test_examples_rules_mode(q, tool, chart):
    ans, mem = ask(q, user_id="group_cfo", model="rules", as_of=AS_OF)
    assert ans.status == "ok", ans.answer_markdown
    assert ans.diagnostics["tool_calls"][0]["name"] == tool
    assert ans.chart_spec.type == chart
    assert ans.table and ans.sql_used and len(ans.followups) == 3
    assert ans.filters_used.get("period") and ans.filters_used.get("currency") == "USD"
    assert mem.get("tool") == tool


def test_followup_uses_memory():
    ans1, mem = ask("How is MAOP YTD vs last year and budget for the United States?", "group_cfo",
                    model="rules", as_of=AS_OF)
    ans2, mem2 = ask("now for Canada", "group_cfo", memory=mem, model="rules", as_of=AS_OF)
    assert ans2.status == "ok"
    assert ans2.filters_used["org_filter"] == {"l3_country": ["Canada"]}
    assert ans2.diagnostics["tool_calls"][0]["name"] == "get_pnl"


def test_ordinal_followup_refers_to_ranked_entity():
    ans1, mem = ask("Which countries have the lowest MAOP margin this year?", "group_cfo", model="rules", as_of=AS_OF)
    first = ans1.table[0]["Country"]
    ans2, _ = ask("why is the first one so low?", "group_cfo", memory=mem, model="rules", as_of=AS_OF)
    assert ans2.status == "ok"
    assert ans2.diagnostics["tool_calls"][0]["name"] == "variance_drivers"
    assert ans2.filters_used["org_filter"] == {"l3_country": [first]}


def test_rls_refusal_never_returns_data():
    ans, _ = ask("How is MAOP YTD for Brazil?", "us_country_head", model="rules", as_of=AS_OF)
    assert ans.status == "refusal"
    assert not ans.table and not ans.sql_used
    assert "access" in ans.answer_markdown.lower()


def test_clarification_for_ambiguous_city():
    from app.semantic.dims import dims
    cities = dims().org.groupby("city")["l5_business"].nunique()
    city = cities[cities > 1].index[0]
    ans, _ = ask(f"How is the {city} business doing?", "group_cfo", model="rules", as_of=AS_OF)
    assert ans.status == "clarification"


def _pnl_call(question: str, args: dict):
    from app.agent.tools import ToolContext, run_tool
    from app.semantic.dims import dims
    from app.semantic.entity_resolver import resolve
    ctx = ToolContext(user_id="group_cfo", as_of=AS_OF, question=question,
                      resolution=resolve(question, dims().org, AS_OF))
    return run_tool("get_pnl", args, ctx)


def test_pnl_bullets_lead_with_the_line_asked_about():
    out = _pnl_call("What is the net income of Mexico this year?", {"org": "Mexico"})
    assert out.bullets[0].startswith("Net income: Actual USD")


def test_llm_actual_only_call_keeps_comparisons_unless_asked():
    # An LLM planner may request Actual only; the user did not, so PY and Budget stay in.
    out = _pnl_call("What is the net income of Mexico this year?", {"org": "Mexico", "versions": ["Actual"]})
    assert out.meta["series"] == ["Actual", "PY", "Budget"]
    out = _pnl_call("What is the actual net income of Mexico this year?", {"org": "Mexico", "versions": ["Actual"]})
    assert out.meta["series"] == ["Actual"]


def test_pnl_states_the_account_asked_about():
    # A single account (restructuring) asked via get_pnl at line depth: the account must still be stated first.
    q = "What restructuring costs did Brazil Environmental Lab Testing book this year?"
    out = _pnl_call(q, {"org": "Brazil Environmental Lab Testing", "account_depth": 1})
    name = out.meta["focus_name"]
    assert name and "estructuring" in name
    assert out.facts[1].startswith(f"{name}: Actual USD") and out.bullets[0].startswith(f"{name}: Actual USD")
    assert not any(f.startswith("MAOP vs") for f in out.facts)     # MAOP drivers do not explain one account


def test_vs_budget_question_keeps_actual_as_main_version():
    # An LLM planner may ask for Budget only; "how is X doing vs budget" still needs Actual first.
    out = _pnl_call("How is Colombia doing vs budget?", {"org": "Colombia", "versions": ["Budget"]})
    assert out.meta["series"] == ["Actual", "Budget"]
    out = _pnl_call("What is the budget for Colombia for 2025?", {"org": "Colombia", "period": "FY 2025",
                                                                   "versions": ["Budget"]})
    assert out.meta["series"] == ["Budget"]


def test_headline_figure_is_the_first_bullet():
    out = _pnl_call("How is the whole group doing this year vs budget?", {"org": "RL Group"})
    assert out.bullets[0].startswith("MAOP: Actual USD")
    from app.agent.tools import ToolContext, run_tool
    q = "Why is Chile Metals & Minerals subcontracting above budget?"
    drv = run_tool("variance_drivers", {"metric": "subcontracting", "org": "Chile Metals & Minerals",
                                        "comparison": "Budget"}, ToolContext(user_id="group_cfo", as_of=AS_OF, question=q))
    assert drv.ok and drv.bullets[0].startswith(drv.meta["name"]) and "Actual USD" in drv.bullets[0]


def test_followup_keeps_the_previous_tool(monkeypatch):
    # "now for Canada" after a P&L question: an LLM that switches to the cockpit is overruled.
    from app.agent import graph, llm
    _, mem = ask("How is MAOP YTD vs last year and budget for the United States?", "group_cfo", model="rules", as_of=AS_OF)
    fake = llm.LLMResult(content="", tool_calls=[{"name": "get_kpi_cockpit", "arguments": {"org": "Canada"}}],
                         native_tool_call=True)
    monkeypatch.setattr(graph.llm, "chat", lambda *a, **k: fake)
    ans, _ = ask("now for Canada", "group_cfo", memory=mem, model="ollama/stub", as_of=AS_OF)
    assert ans.status == "ok" and ans.diagnostics["tool_calls"][0]["name"] == "get_pnl"
    assert "router_followup" in ans.diagnostics["tool_choice_source"]
