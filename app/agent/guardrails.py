"""Guardrails.

1. SQL guard for the fallback tool `run_readonly_sql` (sqlglot):
   exactly one SELECT statement, only whitelisted views from sql/views.sql, no DML/DDL/EXEC,
   no table functions, automatic TOP/LIMIT 1000, 15 s timeout, and in DuckDB mode the
   row-level-security filter is injected into every fact view.
2. Numeric guardrail: every number in the LLM's answer must exist (within display rounding)
   in the tool outputs; otherwise the answer is regenerated once, then replaced by a template.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import pandas as pd
import sqlglot
from sqlglot import exp

from app.config import backend, settings
from app.db import run_with_timeout

WHITELIST = {"v_org", "v_account", "v_period", "v_version", "v_pnl_leaf", "v_pnl", "v_stats"}
RLS_VIEWS = {"v_pnl_leaf", "v_pnl", "v_stats"}
FORBIDDEN_NODES = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Merge,
                   exp.Command, exp.Into, exp.Grant, exp.TruncateTable, exp.Transaction, exp.Commit,
                   exp.Rollback, exp.Set, exp.Use, exp.Pragma, exp.Copy, exp.Describe)
FORBIDDEN_FUNCS = re.compile(r"^(openrowset|openquery|opendatasource|xp_\w*|sp_\w*|read_\w*|"
                             r"glob|load|install|attach|copy|pg_\w*|sqlite_\w*)$", re.I)
ROW_LIMIT = int(settings()["sql_guard"]["row_limit"])
TIMEOUT = int(settings()["sql_guard"]["timeout_seconds"])


class SqlGuardError(ValueError):
    pass


def _dialect() -> str:
    return "duckdb" if backend() == "duckdb" else "tsql"


def validate_sql(sql: str, allowed_bu_ids: set[int] | None = None, dialect: str | None = None) -> str:
    """Return a safe, row-limited SQL string or raise SqlGuardError."""
    dialect = dialect or _dialect()
    if not sql or not sql.strip():
        raise SqlGuardError("empty SQL")
    if re.search(r"\b(exec|execute|xp_cmdshell|sp_executesql|shutdown|dbcc|waitfor|reconfigure)\b", sql, re.I):
        raise SqlGuardError("procedure execution / server commands are not allowed")
    try:
        statements = [s for s in sqlglot.parse(sql, read=dialect) if s is not None]
    except sqlglot.errors.ParseError as exc:
        raise SqlGuardError(f"could not parse SQL: {str(exc).splitlines()[0]}") from exc
    if len(statements) != 1:
        raise SqlGuardError(f"exactly one statement is allowed (got {len(statements)})")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise SqlGuardError(f"only SELECT statements are allowed (got {type(tree).__name__.upper()})")
    for node in tree.walk():
        if isinstance(node, FORBIDDEN_NODES):
            raise SqlGuardError(f"{type(node).__name__.upper()} is not allowed")
        if isinstance(node, (exp.Anonymous, exp.Func)):
            fname = node.name if isinstance(node, exp.Anonymous) else (node.sql_name() or "")
            if FORBIDDEN_FUNCS.match(str(fname)):
                raise SqlGuardError(f"function {fname} is not allowed")
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        if not isinstance(table.this, exp.Identifier):
            raise SqlGuardError("table functions are not allowed")
        name = table.name.lower()
        if name in cte_names and not table.db:
            continue
        if table.catalog or (table.db and table.db.lower() not in ("dbo", "main")):
            raise SqlGuardError(f"cross-database/schema access is not allowed: {table.sql()}")
        if name not in WHITELIST:
            raise SqlGuardError(f"table/view '{name}' is not whitelisted (allowed: {', '.join(sorted(WHITELIST))})")

    # Row-level security in DuckDB mode: wrap each fact view in a filtered subquery
    if allowed_bu_ids is not None:
        ids = ", ".join(str(i) for i in sorted(allowed_bu_ids)) or "-1"

        def _rls(node):
            if isinstance(node, exp.Table) and node.name.lower() in RLS_VIEWS and node.name.lower() not in cte_names:
                alias = node.alias or node.name
                sub = sqlglot.parse_one(f"(SELECT * FROM {node.name} WHERE bu_id IN ({ids})) AS {alias}", read="duckdb")
                return sub
            return node
        tree = tree.transform(_rls)

    # Automatic row limit
    if isinstance(tree, exp.Select):
        limit = tree.args.get("limit")
        current = None
        if limit is not None:
            try:
                current = int(limit.expression.name if hasattr(limit, "expression") and limit.expression else limit.this.name)
            except Exception:  # noqa: BLE001
                current = None
        if current is None or current > ROW_LIMIT:
            tree = tree.limit(ROW_LIMIT)
    else:
        tree = exp.select("*").from_(tree.subquery("q")).limit(ROW_LIMIT)
    return tree.sql(dialect=dialect)


def execute_readonly(engine, safe_sql: str, timeout_s: int = TIMEOUT) -> pd.DataFrame:
    from sqlalchemy import text

    with engine.connect() as conn:
        def _run():
            res = conn.execute(text(safe_sql))
            return pd.DataFrame(res.fetchall(), columns=list(res.keys()))
        df = run_with_timeout(conn, _run, timeout_s)
        conn.rollback()
    for c in df.columns:
        if df[c].dtype == object:
            try:
                df[c] = pd.to_numeric(df[c])
            except (ValueError, TypeError):
                pass
    return df


# ------------------------------------------------------------------------------------------
# Numeric guardrail
# ------------------------------------------------------------------------------------------
NUM_RX = re.compile(
    r"(?<![\w.])[-+−]?\(?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\)?\s*"
    r"(%|pp\b|percentage points?|bn\b|billion|mn\b|million|m\b|k\b|thousand)?", re.I)
SCALE = {"bn": 1e9, "billion": 1e9, "mn": 1e6, "million": 1e6, "m": 1e6, "k": 1e3, "thousand": 1e3}


@dataclass
class NumberToken:
    raw: str
    value: float          # scaled absolute value (percent -> fraction)
    decimals: int
    unit: str
    scale: float


def extract_numbers(text: str) -> list[NumberToken]:
    out = []
    for m in NUM_RX.finditer(text or ""):
        intpart, frac, unit = m.group(1), m.group(2) or "", (m.group(3) or "").lower()
        # skip parts of codes like 7A1, FC2, Q3, R12M, H1 (preceded by a letter) - handled by lookbehind
        nxt = text[m.end():m.end() + 1]
        if not unit and nxt.isalpha():
            continue
        v = float(intpart.replace(",", "") + frac)
        dec = len(frac) - 1 if frac else 0
        if unit in ("%",):
            scale = 0.01
        elif unit.startswith("pp") or unit.startswith("percentage"):
            scale, unit = 0.01, "pp"
        else:
            scale = SCALE.get(unit, 1.0)
        out.append(NumberToken(m.group(0).strip(), abs(v) * scale, dec, unit, scale))
    return out


def _numbers_in(obj, acc: list[float]) -> None:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        if not (isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj))):
            acc.append(abs(float(obj)))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers_in(v, acc)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers_in(v, acc)
    elif isinstance(obj, str):
        acc.extend(t.value for t in extract_numbers(obj))


def allowed_numbers(tool_outputs: list) -> list[float]:
    acc: list[float] = []
    for t in tool_outputs:
        d = t.model_dump() if hasattr(t, "model_dump") else t
        _numbers_in(d.get("facts", []), acc)
        _numbers_in(d.get("data", []), acc)
        _numbers_in(d.get("notes", []), acc)
        _numbers_in(d.get("extra", {}), acc)
        _numbers_in({k: v for k, v in (d.get("meta") or {}).items() if k.startswith("total")}, acc)
        _numbers_in(d.get("filters_used", {}), acc)
    return sorted(set(round(a, 9) for a in acc))


@dataclass
class GuardResult:
    ok: bool
    unsupported: list[str] = field(default_factory=list)
    checked: int = 0


def _is_trivial(tok: NumberToken, question_numbers: set[str]) -> bool:
    if tok.unit == "" and tok.decimals == 0:
        v = tok.value
        if 1990 <= v <= 2100 or v <= 31:          # years, months, days, counts, line numbers
            return True
    return tok.raw.replace("−", "-").strip("+- ()") in question_numbers


def check_numbers(answer: str, tool_outputs: list, question: str = "") -> GuardResult:
    allowed = allowed_numbers(tool_outputs)
    qnums = {t.raw.strip("+- ()") for t in extract_numbers(question or "")}
    bad, checked = [], 0
    for tok in extract_numbers(answer):
        if _is_trivial(tok, qnums):
            continue
        checked += 1
        half_unit = 0.5 * (10 ** -tok.decimals) * tok.scale
        tol = max(half_unit * 1.02, 1e-9)
        ok = any(abs(tok.value - a) <= tol or (tok.value > 0 and abs(tok.value - a) / tok.value <= 0.005)
                 for a in allowed)
        if not ok and tok.unit in ("%", "pp"):
            # model may have written a fraction as percent number without scaling
            ok = any(abs(tok.value * 100 - a) <= tol * 100 for a in allowed)
        if not ok:
            bad.append(tok.raw)
    return GuardResult(ok=not bad, unsupported=bad, checked=checked)
