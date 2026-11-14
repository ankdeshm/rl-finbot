"""Walk through the demo test steps in the real UI with a headless browser and check every expected figure.

    pip install playwright && playwright install chromium     # or run in mcr.microsoft.com/playwright/python
    python scripts/ui_walkthrough.py http://localhost:8501 results/ui_walkthrough [rules,llm]

Rules mode runs every step (expected figures for the as-of date 2026-11-12 in the demo data); LLM mode
(the default model) runs four of them and reads the tool-choice source and guardrail result from
"How I got this". Writes one JSON line per step to walkthrough.jsonl and an element screenshot per answer.
"""
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "results/ui_walkthrough")
PARTS = (sys.argv[3] if len(sys.argv) > 3 else "rules,llm").split(",")
OUT.mkdir(parents=True, exist_ok=True)
BANNED = re.compile(r"\bMAOP\b|\b\d[A-Z]\d\b")            # customer KPI acronym, account codes such as 1A2
CODE_LABEL = re.compile(r"(?m)^\s*\d{1,2}[A-Z]?\d? [A-Za-z]")  # line numbers in front of table labels
MSG = "[data-testid='stChatMessage']"
RESULTS: list[dict] = []


def log(rec: dict) -> None:
    RESULTS.append(rec)
    print(json.dumps(rec), flush=True)


def landing(page) -> None:
    page.wait_for_selector("text=Try one of these", timeout=180_000)
    time.sleep(1.5)


def open_fresh(page, url: str) -> None:
    page.goto(url, wait_until="networkidle")
    landing(page)


def new_conversation(page) -> None:
    page.get_by_role("button", name=re.compile("New conversation")).click()
    landing(page)


def set_persona(page, name: str, access: str) -> None:
    box = page.locator("[data-testid='stSelectbox']").filter(has_text="Persona")
    box.get_by_role("button", name="Open").click()
    page.get_by_role("option", name=name, exact=True).click()
    page.locator("[data-testid='stSidebar']").get_by_text(f"Data access: {access}").wait_for(timeout=60_000)
    landing(page)


def wait_answer(page, before: int, timeout_s: int) -> float:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        msgs = page.locator(MSG)
        if msgs.count() >= before + 2:
            txt = msgs.last.inner_text()
            done = ("Follow-up questions" in txt or "Sorry, you don't have access" in txt
                    or "Something went wrong" in txt or "Which one do you mean" in txt)
            if done and "Analysing the data" not in txt:
                time.sleep(3)
                return time.time() - t0
        time.sleep(0.5)
    raise TimeoutError("answer did not render")


def submit(page, how: str, text: str, timeout_s: int) -> float:
    before = page.locator(MSG).count()
    if how == "button":
        page.get_by_role("button", name=text, exact=True).click()
    else:
        box = page.locator("[data-testid='stChatInputTextArea']")
        box.fill(text)
        box.press("Enter")
    return wait_answer(page, before, timeout_s)


def check(page, step, mode, how, question, expect, forbid=(), timeout_s=60, sidebar=(), code_check=False,
          open_details=False) -> dict:
    rec = {"step": step, "mode": mode, "question": question}
    try:
        secs = submit(page, how, question, timeout_s)
    except Exception as exc:  # noqa: BLE001
        rec.update(ok=False, error=str(exc)[:300])
        page.screenshot(path=str(OUT / f"{mode}_{step}_error.png"))
        log(rec)
        return rec
    last = page.locator(MSG).last
    text = last.inner_text()
    plots = last.locator(".js-plotly-plot")
    blob = text + " " + " ".join(plots.nth(i).text_content() or "" for i in range(plots.count()))
    missing = [e for e in expect if e not in blob]
    present_forbidden = [f for f in forbid if f in blob]
    banned = sorted({m.group(0) for m in BANNED.finditer(blob)})
    rec.update(seconds=round(secs, 1), missing=missing, forbidden=present_forbidden, banned=banned)
    if code_check:
        rec["code_like_labels"] = CODE_LABEL.findall(text)[:5]
    if sidebar:
        sb = page.locator("[data-testid='stSidebar']").inner_text()
        rec["sidebar_missing"] = [s for s in sidebar if s not in sb]
    last.screenshot(path=str(OUT / f"{mode}_{step}.png"))
    if open_details:
        last.locator("summary", has_text="How I got this").click()
        time.sleep(1.5)
        det = last.inner_text()
        m = re.search(r"chosen by:\s*`?([a-z_]+)", det)
        g = re.search(r"Numeric guardrail: ([^·\n]+)· model: ([^·\n]+)· latency: ([0-9.]+)", det)
        rec["tool_choice"] = m.group(1) if m else None
        rec["guardrail"] = g.group(1).strip() if g else None
        rec["model"] = g.group(2).strip() if g else None
        rec["latency_s"] = float(g.group(3)) if g else None
    rec["ok"] = (not missing and not present_forbidden and not rec.get("sidebar_missing")
                 and not rec.get("code_like_labels") and (mode != "rules" or not banned))
    rec["answer_head"] = " ".join(text.split())[:260]
    log(rec)
    return rec


def rules_walk(page) -> None:
    url = f"{BASE}/?model=rules"
    open_fresh(page, url)
    check(page, "1_us_operating_profit", "rules", "button",
          "How is operating profit YTD vs last year and budget for the United States?",
          ["Operating profit", "USD 59.2M", "USD 3.2M (5.8%) above PY", "USD 1.8M", "Operating profit bridge"],
          sidebar=["general ledger (GL)", "constant budget rate"], code_check=True)
    check(page, "2_canada_customer_term", "rules", "typed", "How is MAOP YTD for Canada?",
          ["Operating profit", "USD 18.2M", "USD 6.2M"])
    new_conversation(page)
    check(page, "3_direct_staff_breakdown", "rules", "button",
          "Break down direct staff costs for US Elevators & Pressure Vessels in March 2025",
          ["Direct staff bonus", "Direct staff salaries", "USD 1.6M"], code_check=True)
    set_persona(page, "Environmental Lab Testing PL Leader", "Environmental Lab Testing")
    check(page, "4a_env_rank_countries", "rules", "typed", "Rank countries by operating margin this year",
          ["United States", "Canada", "14.4%", "2.9%", "2 Countries in scope"],
          forbid=["Brazil", "Chile", "Mexico", "Colombia", "Argentina"], sidebar=["Data access: Environmental Lab Testing"])
    set_persona(page, "Group CFO", "RL Group")
    check(page, "4b_canada_env_margin", "rules", "button",
          "Why did Canada Environmental Lab Testing margin drop in 2026?", ["2.9%", "12.7%", "Montreal"])
    new_conversation(page)
    check(page, "5a_monthly_headcount", "rules", "button",
          "Headcount, hires and leavers by month for Canada Environmental Lab Testing this year",
          ["Average headcount: 353", "382", "Leavers: 99", "62 restructuring", "Apr 2026 (63, of which 60 restructuring)",
           "Hires and leavers by month"])
    new_conversation(page)
    check(page, "5b_attrition_by_role", "rules", "button",
          "Attrition by role for Canada Environmental Lab Testing this year vs last year",
          ["33.6%", "10.1%", "Quality", "Lab analyst"])
    check(page, "6a_followup_us", "rules", "typed", "now for the United States",
          ["United States · Environmental Lab Testing", "Average headcount: 31", "5 other roles 0.0%"])
    check(page, "6b_followup_grade", "rules", "typed", "and by grade?", ["By grade", "G1"])
    new_conversation(page)
    check(page, "5c_us_utilization_grade", "rules", "button", "Utilization rate by grade in the United States this year",
          ["73.0%", "G1", "G5"])
    new_conversation(page)
    check(page, "5d_highest_attrition_bus", "rules", "button", "Which BUs have the highest attrition this year?",
          ["CA-ENV-MTL-01", "39.2%", "CA-ENV-CAL-01", "37.1%", "35.8%"])


def llm_walk(page) -> None:
    open_fresh(page, BASE)
    check(page, "1_us_operating_profit", "llm", "button",
          "How is operating profit YTD vs last year and budget for the United States?",
          ["59.2", "3.2", "Operating profit bridge"], timeout_s=600, open_details=True)
    check(page, "2_canada_customer_term", "llm", "typed", "How is MAOP YTD for Canada?", ["18.2", "Operating profit bridge"],
          timeout_s=600, open_details=True)
    new_conversation(page)
    check(page, "5b_attrition_by_role", "llm", "button",
          "Attrition by role for Canada Environmental Lab Testing this year vs last year", ["33.6"],
          timeout_s=600, open_details=True)
    check(page, "6a_followup_us", "llm", "typed", "now for the United States",
          ["United States · Environmental Lab Testing"], timeout_s=600, open_details=True)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 3200})   # tall, so long answers render whole
    for part in PARTS:
        try:
            rules_walk(page) if part == "rules" else llm_walk(page)
        except Exception as exc:  # noqa: BLE001
            log({"part": part, "fatal": str(exc)[:400], "ok": False})
            page.screenshot(path=str(OUT / f"{part}_fatal.png"))
    browser.close()
(OUT / "walkthrough.jsonl").write_text("".join(json.dumps(r) + "\n" for r in RESULTS))
print(f"WALKTHROUGH_DONE {sum(1 for r in RESULTS if r.get('ok'))}/{len(RESULTS)} steps ok", flush=True)
