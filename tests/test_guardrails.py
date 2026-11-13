"""Guardrail tests: SQL guard (read-only, whitelist, limits, RLS injection) and numeric guardrail."""
from __future__ import annotations

import pytest

from app.agent.guardrails import SqlGuardError, check_numbers, execute_readonly, extract_numbers, validate_sql
from app.agent.tools import ToolOutput
from app.config import backend
from app.db import get_engine


@pytest.mark.parametrize("sql", [
    "INSERT INTO v_org VALUES (1)",
    "UPDATE fact_pnl SET amount_usd = 0",
    "DELETE FROM v_pnl",
    "DROP TABLE fact_pnl",
    "EXEC sp_who",
    "SELECT 1; DROP TABLE dim_org",
    "SELECT * INTO hack FROM v_pnl",
    "SELECT * FROM fact_pnl",                       # base tables are not whitelisted
    "SELECT * FROM dim_org",
    "SELECT * FROM read_csv('/etc/passwd')",
    "SELECT * FROM otherdb.dbo.v_pnl",
    "TRUNCATE TABLE fact_pnl",
    "WAITFOR DELAY '00:00:10'",
])
@pytest.mark.parametrize("dialect", ["tsql", "duckdb"])
def test_sql_guard_rejects(sql, dialect):
    with pytest.raises(SqlGuardError):
        validate_sql(sql, dialect=dialect)


@pytest.mark.parametrize("dialect", ["tsql", "duckdb"])
def test_sql_guard_accepts_and_limits(dialect):
    out = validate_sql("SELECT l3_country, SUM(amount_usd) AS v FROM v_pnl WHERE line_no = 13 GROUP BY l3_country",
                       dialect=dialect)
    assert ("TOP 1000" in out.upper()) if dialect == "tsql" else ("LIMIT 1000" in out.upper())
    capped = validate_sql("SELECT * FROM v_pnl_leaf LIMIT 50000", dialect="duckdb")
    assert "LIMIT 1000" in capped.upper()
    cte = validate_sql("WITH x AS (SELECT * FROM v_org) SELECT * FROM x", dialect=dialect)
    assert "v_org" in cte


def test_sql_guard_injects_rls_in_duckdb_mode():
    out = validate_sql("SELECT SUM(amount_usd) FROM v_pnl p WHERE line_no = 6", allowed_bu_ids={1, 2, 3},
                       dialect="duckdb")
    assert "bu_id IN (1, 2, 3)" in out


def test_readonly_execution_respects_limit_and_rls():
    eng = get_engine("us_country_head")
    allowed = None
    if backend() == "duckdb":
        from app.semantic.access import allowed_bus
        allowed = allowed_bus("us_country_head")
    safe = validate_sql("SELECT DISTINCT l3_country FROM v_pnl", allowed_bu_ids=allowed)
    df = execute_readonly(eng, safe)
    assert df.iloc[:, 0].tolist() == ["United States"]
    big = execute_readonly(eng, validate_sql("SELECT * FROM v_pnl_leaf", allowed_bu_ids=allowed))
    assert len(big) == 1000


def _out(facts, data=None):
    return ToolOutput(tool="t", kind="pnl", facts=facts, data=data or [])


def test_numeric_guard_accepts_supported_numbers():
    outs = [_out(["MAOP: USD 23.1M; PY USD 21.6M, difference +USD 1.5M (+6.7%, favourable)",
                  "MAOP margin (on revenue): 11.2%; PY 11.0% (+0.2 pp, favourable)"])]
    answer = ("MAOP for YTD Oct 2026 (Actual) reached USD 23.1M, up USD 1.5M (+6.7%) on PY (USD 21.6M). "
              "The margin improved to 11.2%, +0.2 pp vs last year, in 2026 for the 3 regions.")
    g = check_numbers(answer, outs, "How is MAOP YTD vs last year?")
    assert g.ok, g.unsupported


def test_numeric_guard_flags_invented_numbers():
    outs = [_out(["MAOP: USD 23.1M; PY USD 21.6M"])]
    g = check_numbers("MAOP was USD 25.4M, 17.5% above plan.", outs)
    assert not g.ok and "USD 25.4M".split()[1] in " ".join(g.unsupported) or "25.4M" in " ".join(g.unsupported)
    assert any("17.5" in u for u in g.unsupported)


def test_numeric_guard_uses_table_values():
    outs = [_out([], data=[{"Line": "MAOP", "Actual": 1457687.0}])]
    assert check_numbers("MAOP came in at USD 1,457,687 and USD 1.5M rounded.", outs).ok


def test_number_extraction_units():
    toks = {t.raw: t.value for t in extract_numbers("USD 23.1M, 845k, 11.6%, +4.8 pp, FC2, 7A1 and 2026")}
    assert abs(toks["23.1M"] - 23.1e6) < 1
    assert abs(toks["845k"] - 845e3) < 1
    assert abs(toks["11.6%"] - 0.116) < 1e-9
    assert abs(toks["+4.8 pp"] - 0.048) < 1e-9
    assert not any(k.startswith("2") and "FC" in k for k in toks)


def test_redaction_drops_only_sentences_with_unsupported_numbers():
    from app.agent.graph import redact_sentences
    text = "MAOP is USD 54.4M, USD 3.5M above PY. The gap vs budget is USD 9.9M. Costs rose faster than revenue."
    assert redact_sentences(text, ["9.9M"]) == "MAOP is USD 54.4M, USD 3.5M above PY. Costs rose faster than revenue."
    assert redact_sentences(text, ["<empty>"]) == ""
    # The headline sentence itself is unsupported: use the template instead of a dangling remainder.
    assert redact_sentences(text, ["54.4M"]) == ""
