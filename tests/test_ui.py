"""Headless UI test (Streamlit AppTest): every landing-page example renders an answer with insight
text, a finance table, a chart and three follow-up buttons. Runs without an LLM (LLM_MODEL=rules)."""
from __future__ import annotations

import pytest

from app.config import ROOT

st_testing = pytest.importorskip("streamlit.testing.v1")
APP = str(ROOT / "app" / "ui" / "streamlit_app.py")
N_EXAMPLES = 8


def _run_example(i: int, monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "rules")
    monkeypatch.setenv("LLM_MODEL_CHOICES", "")
    at = st_testing.AppTest.from_file(APP, default_timeout=180)
    at.run()
    assert not at.exception, at.exception
    at.button(key=f"ex_{i}").click().run()
    assert not at.exception, at.exception
    return at


@pytest.mark.parametrize("i", range(N_EXAMPLES))
def test_example_renders_text_table_chart_followups(i, monkeypatch):
    at = _run_example(i, monkeypatch)
    md = [m.value for m in at.markdown]
    assert any("fin-table" in v for v in md), "finance table missing"
    assert len(at.get("plotly_chart")) >= 1, "chart missing"
    answer_texts = [v for v in md if len(v) > 60 and "fin-table" not in v and "<div" not in v and "<style" not in v]
    assert answer_texts, "insight text missing"
    followups = [b for b in at.button if b.key and b.key.startswith("fu_")]
    assert len(followups) == 3, [b.key for b in at.button]
    chips = [v for v in md if "<span class='rl-chip'>" in v]
    assert chips and "USD" in chips[0], "filters / currency chips missing"


def test_followup_button_runs_second_turn(monkeypatch):
    at = _run_example(0, monkeypatch)
    fu = [b for b in at.button if b.key and b.key.startswith("fu_")][0]
    fu.click().run()
    assert not at.exception, at.exception
    assert len(at.chat_message) == 4                     # two questions, two answers


def test_restricted_persona_gets_refusal(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "rules")
    at = st_testing.AppTest.from_file(APP, default_timeout=180)
    at.run()
    at.selectbox[0].select("United States Country Head").run()
    at.chat_input[0].set_value("How is MAOP YTD for Brazil?").run()
    assert not at.exception, at.exception
    assert any("rl-refusal" in m.value for m in at.markdown)
