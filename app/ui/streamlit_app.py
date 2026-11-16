"""RL Certification & Inspection - Finance Copilot (Streamlit UI).

Every answer renders: insight text, finance table, deterministic chart, "How I got this"
(filters, version, period, SQL), three follow-up buttons and CSV / Excel downloads.
"""
from __future__ import annotations

import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from app.config import backend, data_as_of_date, env, settings  # noqa: E402

st.set_page_config(page_title="RL Finance Copilot", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

from app.agent.graph import ask  # noqa: E402
from app.semantic import time_intel as ti  # noqa: E402
from app.semantic.access import scope_label  # noqa: E402
from app.viz.charts import figure  # noqa: E402
from app.viz.tables import TABLE_CSS, render_html, to_csv_bytes, to_excel_bytes  # noqa: E402

COMPANY = settings().get("company_long", "RL Certification & Inspection")
CUR = settings().get("currency", "USD")
PERSONAS = {
    "Group CFO": "group_cfo",
    "United States Country Head": "us_country_head",
    "Environmental Lab Testing PL Leader": "env_pl_leader",
}
EXAMPLES = [
    "How is operating profit YTD vs last year and budget for the United States?",
    "Show personnel cost as % of revenue trend for Environmental Lab Testing since 2023",
    "Why did Canada Environmental Lab Testing margin drop in 2026?",
    "Top 5 BUs by operating margin in US & Canada this year",
    "Compare Budget vs FC2 vs Actual for Chile Metals & Minerals",
    "Break down direct staff costs for US Elevators & Pressure Vessels in March 2025",
    "What happened to WIP in Mexico Buildings & Infrastructure this year?",
    "Subcontracting cost by product line YTD vs PY",
]
WORKFORCE_EXAMPLES = [
    "Headcount, hires and leavers by month for Canada Environmental Lab Testing this year",
    "Attrition by role for Canada Environmental Lab Testing this year vs last year",
    "Utilization rate by grade in the United States this year",
    "Which BUs have the highest attrition this year?",
]
EXTRA_EXAMPLES = [
    "Show the operational profitability cockpit for Canada",
    "What is the utilization rate in Mexico vs budget?",
]

CSS = """
<style>
html, body, [class*="css"] {font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif;}
.block-container {padding-top: 1.2rem; max-width: 1350px;}
.rl-header {background: linear-gradient(90deg, #0B3D91 0%, #1F5FBF 100%); color: #fff; padding: 14px 20px;
            border-radius: 10px; margin-bottom: 10px;}
.rl-header h1 {font-size: 1.45rem; margin: 0; color: #fff; font-weight: 700;}
.rl-header p {margin: 2px 0 0 0; font-size: 0.9rem; opacity: 0.9;}
.rl-banner {background: #FFF4E5; border: 1px solid #F5B041; color: #7E5109; padding: 6px 12px; border-radius: 8px;
            font-size: 0.85rem; margin-bottom: 10px;}
.rl-scope {font-size: 0.8rem; color: #5D6D7E;}
.rl-chip {display:inline-block; background:#EAF2FB; color:#0B3D91; border-radius:12px; padding:2px 10px;
          margin:2px 4px 2px 0; font-size:0.78rem;}
.rl-refusal {background:#FDEDEC; border-left: 4px solid #C0392B; padding: 8px 12px; border-radius: 6px;}
div[data-testid="stChatMessage"] {background: #FFFFFF;}
.stButton>button {border-radius: 8px; border: 1px solid #D6DBDF; text-align: left; white-space: normal;
                  height: auto; padding: 0.45rem 0.7rem; font-size: 0.86rem;}
.stButton>button:hover {border-color: #0B3D91; color: #0B3D91;}
</style>
"""


def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("memory", {})
    st.session_state.setdefault("pending", None)
    st.session_state.setdefault("persona", "Group CFO")


def model_choices() -> list[str]:
    current = env("LLM_MODEL", "ollama/qwen2.5-coder:14b")
    raw = env("LLM_MODEL_CHOICES", "") or ""
    choices = [current] + [m.strip() for m in raw.split(",") if m.strip() and m.strip() != current]
    return choices + ["rules (no LLM)"]


def sidebar() -> dict:
    with st.sidebar:
        st.markdown(f"### 📊 {COMPANY}")
        st.caption("Finance Copilot · general ledger (GL) management P&L")
        persona = st.selectbox("Persona", list(PERSONAS), index=list(PERSONAS).index(st.session_state.persona))
        if persona != st.session_state.persona:
            st.session_state.persona = persona
            st.session_state.memory = {}
            st.session_state.messages = []
            st.rerun()
        user_id = PERSONAS[persona]
        st.markdown(f"<div class='rl-scope'>Data access: <b>{scope_label(user_id)}</b></div>", unsafe_allow_html=True)
        max_d = data_as_of_date()
        as_of = st.date_input("As-of date", value=max_d, min_value=date(2022, 2, 6), max_value=max_d,
                              help="Moves the point in time back: closed months and available forecasts follow.")
        choices = model_choices()
        wanted = str(st.query_params.get("model", "")).strip().lower()
        idx = next((i for i, c in enumerate(choices) if wanted and c.lower().startswith(wanted)), 0)
        model = st.selectbox("Model (LiteLLM)", choices, index=idx,
                             help="'rules (no LLM)' uses the deterministic router and templated text.")
        units = st.radio("Units", [f"{CUR} k", f"{CUR} M"], horizontal=True, index=0)
        st.divider()
        if st.button("🧹 New conversation", width="stretch"):
            st.session_state.messages, st.session_state.memory = [], {}
            st.rerun()
        last = ti.last_closed_month(as_of)
        st.caption(f"Backend: {backend()} · last closed month: {ti.month_label(last)} · {CUR} at "
                   f"{settings().get('fx_rate_label', 'constant budget rate')}")
    return {"user_id": user_id, "as_of": as_of, "model": None if model.startswith("rules") else model,
            "model_label": model, "units": "M" if units.endswith("M") else "k"}


def header() -> None:
    st.markdown(f"<div class='rl-header'><h1>{COMPANY} · Finance Copilot</h1>"
                "<p>Ask finance questions in plain English: P&amp;L, variances, ratios, rankings, versions, "
                "KPI cockpit and workforce. Every number comes from the database, never from the language model.</p></div>",
                unsafe_allow_html=True)
    st.markdown("<div class='rl-banner'>⚠️ <b>Synthetic data – prototype.</b> Fictional company, people and figures; "
                "for demonstration only.</div>", unsafe_allow_html=True)


def _example_buttons(questions: list[str], prefix: str, ncols: int = 2) -> None:
    cols = st.columns(ncols)
    for i, q in enumerate(questions):
        if cols[i % ncols].button(q, key=f"{prefix}_{i}", width="stretch"):
            st.session_state.pending = q
            st.rerun()


def landing() -> None:
    st.markdown("#### Try one of these")
    _example_buttons(EXAMPLES, "ex")
    st.markdown("#### Workforce (new): fictional employee records")
    _example_buttons(WORKFORCE_EXAMPLES, "exw")
    with st.expander("More examples (KPI cockpit)"):
        _example_buttons(EXTRA_EXAMPLES, "exx", 1)


def render_answer(ans: dict, idx: int, cfg: dict) -> None:
    status = ans.get("status", "ok")
    if status == "refusal":
        st.markdown(f"<div class='rl-refusal'>🔒 {ans['answer_markdown']}</div>", unsafe_allow_html=True)
    elif status == "clarification":
        st.info(ans["answer_markdown"])
        d = ans.get("diagnostics", {})
        as_question = d.get("options_mode") == "question"    # "Show revenue instead", "Use last month instead"
        for j, opt in enumerate(d.get("options", [])[:6]):
            if st.button(opt, key=f"opt_{idx}_{j}"):
                st.session_state.pending = opt if as_question else f"{opt}: {d.get('question', '')}".strip(": ")
                st.rerun()
    else:
        st.markdown(ans["answer_markdown"])
    f = ans.get("filters_used") or {}
    chips = [x for x in (f.get("org"), f.get("period"), ", ".join(f.get("versions", [])[:4]) if f.get("versions") else None,
                         f.get("currency")) if x]
    if chips and status == "ok":
        st.markdown("".join(f"<span class='rl-chip'>{c}</span>" for c in chips), unsafe_allow_html=True)
    if f.get("carried_over") and status == "ok":
        st.caption("↪ Carried over: " + " · ".join(f["carried_over"]))
    tspec = ans.get("table_spec") or {}
    if tspec.get("columns"):
        st.markdown(TABLE_CSS + render_html(tspec, cfg["units"]), unsafe_allow_html=True)
        for extra in tspec.get("extra_tables", []):
            with st.expander(extra.get("caption", "Detail")):
                st.markdown(TABLE_CSS + render_html(extra, cfg["units"]), unsafe_allow_html=True)
    fig = figure(ans.get("chart_spec") or {}, cfg["units"])
    if fig is not None:
        st.plotly_chart(fig, width="stretch", key=f"chart_{idx}")
    if tspec.get("columns"):
        c1, c2, _ = st.columns([1, 1, 4])
        c1.download_button("⬇️ CSV", to_csv_bytes(tspec), file_name=f"rl_answer_{idx}.csv", mime="text/csv",
                           key=f"csv_{idx}")
        c2.download_button("⬇️ Excel", to_excel_bytes(tspec), file_name=f"rl_answer_{idx}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xls_{idx}")
    if status in ("ok", "refusal"):
        with st.expander("🔍 How I got this"):
            d = ans.get("diagnostics", {})
            st.markdown(f"**Scope:** {f.get('org', '-')}  \n**Period:** {f.get('period', '-')} "
                        f"({f.get('months', '')})  \n**Versions:** {', '.join(f.get('versions', [])) or '-'}  \n"
                        f"**Currency:** {f.get('currency', CUR)} · **As-of:** {f.get('as_of_date', '-')} · "
                        f"**Row-level security:** {f.get('rls', '-')}")
            for n in f.get("notes", []) or []:
                st.caption(f"Note: {n}")
            calls = d.get("tool_calls") or []
            if calls:
                st.markdown("**Tool calls** (chosen by: `" + str(d.get("tool_choice_source")) + "`)")
                st.json(calls, expanded=False)
            g = d.get("guardrail") or {}
            if g:
                st.caption(f"Numeric guardrail: {'passed' if g.get('ok') and not g.get('template') else ('templated answer used' if g.get('template') else 'failed')} "
                           f"· model: {d.get('model') or 'rules'} · latency: {d.get('latency_s', '-')} s")
            for i, sql in enumerate(ans.get("sql_used") or []):
                st.code(sql, language="sql")
    fu = ans.get("followups") or []
    if fu and status == "ok":
        st.markdown("**Follow-up questions**")
        cols = st.columns(3)
        for j, q in enumerate(fu[:3]):
            if cols[j].button(q, key=f"fu_{idx}_{j}", width="stretch"):
                st.session_state.pending = q
                st.rerun()


def process(question: str, cfg: dict) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Analysing the data ..."):
            t0 = time.time()
            try:
                ans, mem = ask(question, user_id=cfg["user_id"], memory=st.session_state.memory,
                               model=cfg["model"] or "rules", as_of=cfg["as_of"])
                payload = ans.model_dump()
                payload["diagnostics"]["question"] = question
                st.session_state.memory = mem
            except Exception as exc:  # noqa: BLE001
                payload = {"answer_markdown": f"Something went wrong: {exc}", "status": "error", "followups": [],
                           "diagnostics": {"latency_s": round(time.time() - t0, 1)}}
    st.session_state.messages.append({"role": "assistant", "answer": payload})
    st.rerun()


def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    cfg = sidebar()
    header()
    if not st.session_state.messages and not st.session_state.pending:
        landing()
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"], avatar="🧑‍💼" if m["role"] == "user" else "📊"):
            if m["role"] == "user":
                st.markdown(m["content"])
            else:
                render_answer(m["answer"], i, cfg)
    typed = st.chat_input("Ask a finance question, e.g. 'How is operating profit YTD vs budget for Mexico?'")
    q = typed or st.session_state.pending
    if q:
        st.session_state.pending = None
        process(q, cfg)


main()
