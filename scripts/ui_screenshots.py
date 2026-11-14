"""Capture screenshots of the running UI: the landing page and one answer per example question.

    pip install playwright && playwright install chromium     # or run in mcr.microsoft.com/playwright/python
    python scripts/ui_screenshots.py "http://localhost:8501/?model=rules" results/ui_screenshots/rules_mode
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501/?model=rules"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "results/ui_screenshots/rules_mode")
QUESTIONS = [
    "How is operating profit YTD vs last year and budget for the United States?",
    "Why did Canada Environmental Lab Testing margin drop in 2026?",
    "Top 5 BUs by operating margin in US & Canada this year",
    "Compare Budget vs FC2 vs Actual for Chile Metals & Minerals",
    "Break down direct staff costs for US Elevators & Pressure Vessels in March 2025",
    "What happened to WIP in Mexico Buildings & Infrastructure this year?",
    "Show personnel cost as % of revenue trend for Environmental Lab Testing since 2023",
    "Subcontracting cost by product line YTD vs PY",
    "Headcount, hires and leavers by month for Canada Environmental Lab Testing this year",
    "Attrition by role for Canada Environmental Lab Testing this year vs last year",
    "Utilization rate by grade in the United States this year",
    "Which BUs have the highest attrition this year?",
]


def wait_answer(page, timeout_s: int = 900) -> float:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if page.locator("text=Follow-up questions").count() > 0 and page.locator(".js-plotly-plot").count() > 0:
            time.sleep(4)
            return time.time() - t0
        time.sleep(1)
    raise TimeoutError("answer did not render")


OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_selector("text=Try one of these", timeout=180_000)
    time.sleep(2)
    page.screenshot(path=str(OUT / "00_landing.png"), full_page=True)
    print("landing ok", flush=True)
    page.set_viewport_size({"width": 1440, "height": 2600})
    for i, q in enumerate(QUESTIONS, 1):
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("text=Try one of these", timeout=180_000)
        page.get_by_role("button", name=q, exact=True).click()
        secs = wait_answer(page)
        page.screenshot(path=str(OUT / f"{i:02d}_answer.png"))
        text = " ".join(page.locator("[data-testid='stChatMessage']").last.inner_text().split())
        print(f"{i:02d} {secs:.0f}s {q}\n    {text[:400]}", flush=True)
    browser.close()
