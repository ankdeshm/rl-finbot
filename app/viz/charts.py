"""Deterministic chart selection (never decided by the LLM) and Plotly rendering.

trend -> line (Actual vs PY vs Budget, R12M dashed) | variance / bridge -> waterfall |
cost mix / break down -> stacked bar | ranking -> horizontal bar | ratio -> bar |
version comparison -> grouped bar
"""
from __future__ import annotations

import plotly.graph_objects as go

from app.viz import format as F

COLORS = {"Actual": "#0B3D91", "PY": "#A6ACAF", "Budget": "#E67E22", "FC1": "#85C1E9",
          "FC2": "#2E86C1", "FC3": "#1B4F72", "Actual R12M": "#17A589"}
FAV, UNFAV, NEUTRAL, TOTAL = "#1E8449", "#C0392B", "#7F8C8D", "#0B3D91"
SERIES_PALETTE = ["#0B3D91", "#2E86C1", "#85C1E9", "#E67E22", "#F5B041", "#17A589", "#76D7C4",
                  "#7D3C98", "#BB8FCE", "#A6ACAF"]


def _none(reason: str = "") -> dict:
    return {"type": "none", "title": reason, "data": [], "fmt": "eur", "x": None, "y": [], "meta": {}}


def chart_spec(out: dict, intents: list[str] | None = None) -> dict:
    intents = intents or []
    if not out or not out.get("ok", True):
        return _none()
    kind, data, meta, f = out.get("kind"), out.get("data") or [], out.get("meta") or {}, out.get("filters_used") or {}
    period, org = f.get("period", ""), f.get("org", "")
    if kind == "trend":
        return {"type": "line", "title": f"{meta.get('name')} - {org} ({period})", "fmt": meta.get("fmt", "eur"),
                "x": "Month", "y": meta.get("series", []), "data": data, "meta": {}}
    if kind == "pnl":
        return _pnl_bridge(data, meta, org, period)
    if kind == "cockpit":
        trend = (out.get("extra") or {}).get("trend") or []
        return {"type": "combo", "title": f"Direct margin by month - {org} (Actual bars, LY and Budget lines)",
                "fmt": "pct", "x": "Month", "y": ["Actual", "PY", "Budget"], "data": trend,
                "meta": {"bars": ["Actual"], "lines": ["PY", "Budget"]}}
    if kind == "drivers":
        return _drivers_chart(out, intents)
    if kind == "ranking":
        cur = meta.get("current", "Actual")
        lvl = meta.get("level_label", "Entity")
        rows = [{"label": str(r[lvl]), "value": r.get(cur), "fav": r.get("_fav")} for r in data if r.get(cur) is not None]
        return {"type": "hbar", "title": f"{meta.get('name')} by {lvl} - {org} ({period})", "fmt": meta.get("fmt", "eur"),
                "x": "value", "y": ["label"], "data": rows, "meta": {"ascending": meta.get("ascending")}}
    if kind == "ratio":
        name = meta.get("name")
        rows = [{"label": f"{r['Version']} ({r['Period']})", "value": r.get(name)} for r in data]
        return {"type": "bar", "title": f"{name} - {org}", "fmt": meta.get("fmt", "pct"), "x": "label",
                "y": ["value"], "data": rows, "meta": {}}
    if kind == "versions":
        labels = meta.get("series", [])
        sign = {"production": 1, "personnel": -1, "subcontracting": -1, "other_cost": -1, "functional_cost": -1,
                "gross_profit": 1, "maop": 1}
        rows = []
        for r in data:
            if r.get("_code") in sign:
                for lab in labels:
                    rows.append({"category": r["Line"].title() if r["Line"].isupper() else r["Line"],
                                 "series": lab, "value": (r.get(lab) or 0) * sign[r["_code"]]})
        return {"type": "grouped_bar", "title": f"Versions - {org} ({period}), costs shown as positive amounts",
                "fmt": "eur", "x": "category", "y": labels, "data": rows, "meta": {}}
    if kind == "sql" and data:
        cols = list(data[0].keys())
        text_cols = [c for c in cols if isinstance(data[0][c], str)]
        num_cols = [c for c in cols if isinstance(data[0][c], (int, float)) and not isinstance(data[0][c], bool)]
        if text_cols and num_cols and len(data) <= 40:
            rows = [{"label": str(r[text_cols[0]]), "value": r[num_cols[0]]} for r in data]
            return {"type": "bar", "title": f"{num_cols[0]} by {text_cols[0]}", "fmt": "num", "x": "label",
                    "y": ["value"], "data": rows, "meta": {}}
    return _none()


def _pnl_bridge(data, meta, org, period) -> dict:
    by = {r["_code"]: r for r in data}
    labels = meta.get("series", ["Actual"])
    primary = labels[0]
    cmp_ = "PY" if "PY" in labels[1:] else (labels[1] if len(labels) > 1 else None)
    steps = [("6", "Production"), ("7", "Personnel"), ("8", "Ext. subcontracting"), ("9", "Other costs"),
             ("10", "Functional neutr."), ("12", "Functional costs")]
    if "13" not in by:
        return _none()
    rows = []
    if cmp_:
        rows.append({"label": f"MAOP {cmp_}", "value": by["13"][cmp_], "measure": "absolute"})
        for code, name in steps:
            if code in by and by[code].get(f"Var vs {cmp_}") is not None:
                rows.append({"label": name, "value": by[code][f"Var vs {cmp_}"], "measure": "relative"})
        rows.append({"label": f"MAOP {primary}", "value": by["13"][primary], "measure": "total"})
        title = f"MAOP bridge {cmp_} to {primary} - {org} ({period})"
    else:
        rows.append({"label": "Production", "value": by["6"][primary], "measure": "absolute"})
        for code, name in steps[1:]:
            rows.append({"label": name, "value": by[code][primary], "measure": "relative"})
        rows.append({"label": "MAOP", "value": by["13"][primary], "measure": "total"})
        title = f"Production to MAOP - {org} ({period})"
    return {"type": "waterfall", "title": title, "fmt": "eur", "x": "label", "y": ["value"], "data": rows,
            "meta": {"favorable": "up"}}


def _drivers_chart(out: dict, intents: list[str]) -> dict:
    meta, data = out.get("meta") or {}, out.get("data") or []
    org_rows = (out.get("extra") or {}).get("org") or []
    f = out.get("filters_used") or {}
    cur, cmp_ = meta.get("current", "Actual"), meta.get("comparison", "PY")
    unit = meta.get("unit", "eur")
    fmt = "pct" if unit == "pp" else meta.get("fmt", "eur")
    name = meta.get("name", "")
    title_tail = f"{f.get('org', '')} ({f.get('period', '')})"
    if data and "breakdown" in intents and unit == "eur":
        rows = []
        for r in data:
            rows.append({"category": f"{cmp_}", "series": r["Driver"], "value": r.get(cmp_)})
            rows.append({"category": f"{cur}", "series": r["Driver"], "value": r.get(cur)})
        return {"type": "stacked_bar", "title": f"{name} mix: {cmp_} vs {cur} - {title_tail}", "fmt": "eur",
                "x": "category", "y": [r["Driver"] for r in data], "data": rows, "meta": {}}
    source = data if data else ([] if meta.get("kind") == "ratio" else org_rows)
    if source:
        label_key = "Driver" if data else [k for k in org_rows[0] if k not in (cur, cmp_, "Impact", "_fav")][0]
        top = sorted(source, key=lambda r: abs(r.get("Impact") or 0), reverse=True)
        main, rest = top[:6], top[6:]
        rows = [{"label": f"{name} {cmp_}", "value": meta.get("total_comparison"), "measure": "absolute"}]
        for r in main:
            rows.append({"label": str(r[label_key]).replace(" as % of revenue", "").replace(" as % of production", ""),
                         "value": r.get("Impact") or 0, "measure": "relative"})
        if rest:
            rows.append({"label": "Other", "value": sum(r.get("Impact") or 0 for r in rest), "measure": "relative"})
        rows.append({"label": f"{name} {cur}", "value": meta.get("total_current"), "measure": "total"})
        return {"type": "waterfall", "title": f"{name}: {cmp_} to {cur} - {title_tail}", "fmt": fmt,
                "x": "label", "y": ["value"], "data": rows, "meta": {"favorable": meta.get("favorable", "up")}}
    if org_rows:
        lvl = [k for k in org_rows[0] if k not in (cur, cmp_, "Impact", "_fav")][0]
        rows = [{"label": str(r[lvl]), "value": r.get("Impact"), "fav": r.get("_fav")} for r in org_rows]
        return {"type": "hbar", "title": f"{name} change vs {cmp_} by {lvl.lower()} - {title_tail}",
                "fmt": fmt if fmt != "pct" else "pp", "x": "value", "y": ["label"], "data": rows, "meta": {}}
    return _none()


# ------------------------------------------------------------------------------------------
# Rendering
# ------------------------------------------------------------------------------------------
def _scale(fmt: str, units: str, data=None) -> tuple[float, str]:
    if fmt == "eur":
        vals = [abs(r.get("value") or 0) for r in (data or []) if isinstance(r.get("value"), (int, float))]
        if vals and max(vals) < 5000:                      # per-hour / per-FTE style amounts
            return 1.0, F.CUR
        return (1e6, F.unit_label("M")) if units == "M" else (1e3, F.unit_label("k"))
    return 1.0, ""


def _tickformat(fmt: str) -> str | None:
    return ".1%" if fmt in ("pct", "pp") else None


def waterfall_range(ys: list, measures: list) -> list | None:
    """Value-axis range for a bridge whose steps are small next to its totals (None = autorange).

    Finance bridges such as MAOP PY -> Actual have totals far from zero and steps of a few percent;
    starting the axis at zero makes the steps unreadable. The axis is zoomed only when every running
    level is positive and the lowest level is at least 35% of the highest.
    """
    level, pts = 0.0, []
    for y, m in zip(ys, measures):
        y = y or 0.0
        if m == "absolute":
            level = y
            pts.append(level)
        elif m == "total":
            pts.append(level)
        else:
            pts.append(level)
            level += y
            pts.append(level)
    if not pts:
        return None
    lo, hi = min(pts), max(pts)
    span = hi - lo
    if lo <= 0 or span <= 0 or lo < 0.35 * hi:
        return None
    return [max(0.0, lo - span), hi + 0.3 * span]


def figure(spec: dict, units: str = "M") -> go.Figure | None:
    t = spec.get("type")
    if not t or t == "none":
        return None
    fmt = spec.get("fmt", "eur")
    scale, unit_lbl = _scale(fmt, units, spec.get("data"))
    data = spec.get("data", [])
    fig = go.Figure()

    def sv(v):
        return None if v is None else v / scale

    def lbl(v):
        if v is None:
            return ""
        if fmt == "eur":
            return f"{v / scale:,.{1 if (units == 'M' or scale == 1.0) else 0}f}"
        if fmt in ("pct", "pp"):
            return f"{v * 100:.1f}%"
        return f"{v:,.1f}"

    zoom = None
    if t == "line":
        for s in spec.get("y", []):
            ys = [sv(r.get(s)) for r in data]
            fig.add_trace(go.Scatter(x=[r[spec["x"]] for r in data], y=ys, mode="lines+markers", name=s,
                                     line={"color": COLORS.get(s), "width": 3 if s == "Actual" else 2,
                                           "dash": "dash" if s in ("Budget", "Actual R12M") else ("dot" if s == "PY" else "solid")},
                                     connectgaps=False))
    elif t == "waterfall":
        fav_dir = spec.get("meta", {}).get("favorable", "up")
        inc, dec = (FAV, UNFAV) if fav_dir != "down" else (UNFAV, FAV)
        fig.add_trace(go.Waterfall(
            x=[r["label"] for r in data], measure=[r["measure"] for r in data], y=[sv(r["value"]) for r in data],
            text=[lbl(r["value"]) for r in data], textposition="outside",
            increasing={"marker": {"color": inc}}, decreasing={"marker": {"color": dec}},
            totals={"marker": {"color": TOTAL}}, connector={"line": {"color": "#BDC3C7"}}))
        zoom = waterfall_range([sv(r["value"]) for r in data], [r["measure"] for r in data])
    elif t == "stacked_bar":
        series = list(dict.fromkeys(r["series"] for r in data))
        for i, s in enumerate(series):
            rows = [r for r in data if r["series"] == s]
            fig.add_trace(go.Bar(x=[r["category"] for r in rows], y=[sv(r["value"]) for r in rows], name=s,
                                 marker_color=SERIES_PALETTE[i % len(SERIES_PALETTE)]))
        fig.update_layout(barmode="stack")
    elif t == "hbar":
        rows = list(reversed(data))
        colors = [FAV if r.get("fav") is True else (UNFAV if r.get("fav") is False else TOTAL) for r in rows] \
            if fmt == "pp" else TOTAL
        fig.add_trace(go.Bar(y=[r["label"] for r in rows], x=[sv(r["value"]) for r in rows], orientation="h",
                             marker_color=colors, text=[lbl(r["value"]) for r in rows], textposition="auto"))
    elif t == "bar":
        fig.add_trace(go.Bar(x=[r["label"] for r in data], y=[sv(r["value"]) for r in data],
                             marker_color=[COLORS.get(str(r["label"]).split(" ")[0], TOTAL) for r in data],
                             text=[lbl(r["value"]) for r in data], textposition="outside"))
    elif t == "combo":
        meta = spec.get("meta", {})
        for s in meta.get("bars", []):
            fig.add_trace(go.Bar(x=[r[spec["x"]] for r in data], y=[sv(r.get(s)) for r in data], name=s,
                                 marker_color=COLORS.get(s), text=[lbl(r.get(s)) for r in data],
                                 textposition="outside"))
        for s in meta.get("lines", []):
            fig.add_trace(go.Scatter(x=[r[spec["x"]] for r in data], y=[sv(r.get(s)) for r in data], name=s,
                                     mode="lines+markers", line={"color": COLORS.get(s),
                                                                 "dash": "dash" if s == "Budget" else "dot"}))
    elif t == "grouped_bar":
        series = spec.get("y", [])
        for s in series:
            rows = [r for r in data if r["series"] == s]
            fig.add_trace(go.Bar(x=[r["category"] for r in rows], y=[sv(r["value"]) for r in rows], name=s,
                                 marker_color=COLORS.get(s)))
        fig.update_layout(barmode="group")
    fig.update_layout(
        title={"text": spec.get("title", ""), "font": {"size": 15}}, template="plotly_white", height=430,
        margin={"l": 40, "r": 20, "t": 60, "b": 40}, legend={"orientation": "h", "y": -0.18},
        font={"family": "Inter, Segoe UI, Helvetica, Arial, sans-serif", "size": 12}, showlegend=t != "waterfall")
    axis = "xaxis" if t == "hbar" else "yaxis"
    if _tickformat(fmt):
        fig.update_layout(**{axis: {"tickformat": _tickformat(fmt)}})
    elif unit_lbl:
        fig.update_layout(**{axis: {"title": unit_lbl, "tickformat": ",.1f" if (units == "M" and scale != 1.0) else ",.0f"}})
    if zoom:
        fig.update_yaxes(range=zoom)
    return fig
