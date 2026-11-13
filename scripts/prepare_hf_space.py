"""Prepare a Hugging Face Spaces bundle (Docker SDK) in hf_space/ that runs the app on the DuckDB
backend, so a public demo needs neither SQL Server nor a local LLM.

    uv run python scripts/prepare_hf_space.py --model gemini/gemini-2.5-flash

Requires data/rl_finbot.duckdb (`make data duckdb`). Nothing is uploaded: the script prints the
git commands to push the folder to a Space you own. Set the LLM key (e.g. GEMINI_API_KEY) as a
Space secret, never in the files.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hf_space"
COPY = ["app", "config", "sql", "scripts", "pyproject.toml", "uv.lock", "Dockerfile", ".env.example"]

README = """---
title: RL Finance Copilot
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8501
pinned: false
---

# RL Finance Copilot (synthetic data)

Conversational finance analytics over a synthetic AD50 management P&L of a fictional Testing,
Inspection & Certification company. DuckDB backend; the LLM is `{model}`.
All figures are synthetic.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini/gemini-2.5-flash")
    args = ap.parse_args()
    duck = ROOT / "data" / "rl_finbot.duckdb"
    if not duck.exists():
        raise SystemExit("data/rl_finbot.duckdb not found - run `make data duckdb` first")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name in COPY:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, OUT / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif src.exists():
            shutil.copy2(src, OUT / name)
    (OUT / "data").mkdir()
    shutil.copy2(duck, OUT / "data" / duck.name)
    (OUT / "Makefile").write_text("run:\n\tstreamlit run app/ui/streamlit_app.py\n")
    (OUT / "README.md").write_text(README.format(model=args.model))
    df = (OUT / "Dockerfile").read_text()
    df = df.replace("ENV PYTHONDONTWRITEBYTECODE=1",
                    f"ENV DB_BACKEND=duckdb \\\n    DUCKDB_PATH=data/rl_finbot.duckdb \\\n    LLM_MODEL={args.model} \\\n"
                    "    PYTHONDONTWRITEBYTECODE=1")
    (OUT / "Dockerfile").write_text(df)
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"hf_space/ ready ({size:.0f} MB). To publish to a Space you own:")
    print("  cd hf_space && git init && git lfs track '*.duckdb' && git add . && git commit -m 'RL Finance Copilot'")
    print("  git remote add origin https://huggingface.co/spaces/<user>/<space> && git push -u origin main")
    print("  then set the LLM key (e.g. GEMINI_API_KEY) as a Space secret.")


if __name__ == "__main__":
    main()
