"""User Guide page: renders docs/user_guide.md (the single source, so the page and the file stay identical).

Gallery lines between the `gallery:start` / `gallery:end` markers become buttons that send the question to
Chat; image lines are shown from docs/img/.
"""
from __future__ import annotations

import re

import streamlit as st

from app.config import ROOT

GUIDE = ROOT / "docs" / "user_guide.md"
IMG_RX = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)\s*$")
GALLERY_RX = re.compile(r"^- \*\*(?P<intent>[^:*]+):\*\* (?P<q>.+)$")


def gallery_items(text: str) -> list[tuple[str, str]]:
    block = text.split("<!-- gallery:start -->", 1)[-1].split("<!-- gallery:end -->", 1)[0]
    return [(m["intent"].strip(), m["q"].strip()) for m in map(GALLERY_RX.match, block.splitlines()) if m]


def _queue(question: str) -> None:
    st.session_state.pending = question
    st.session_state.nav_goto = "chat"


def _gallery(items: list[tuple[str, str]]) -> None:
    intents = list(dict.fromkeys(i for i, _ in items))
    cols = st.columns(2)
    for n, intent in enumerate(intents):
        with cols[n % 2]:
            st.markdown(f"**{intent}**")
            for j, (i, q) in enumerate(items):
                if i == intent:
                    st.button(q, key=f"guide_{j}", on_click=_queue, args=(q,), width="stretch")


def _flush(buf: list[str]) -> None:
    if any(line.strip() for line in buf):
        st.markdown("\n".join(buf))
    buf.clear()


def render() -> None:
    if not GUIDE.exists():
        st.warning("docs/user_guide.md is missing.")
        return
    text = GUIDE.read_text(encoding="utf-8")
    buf: list[str] = []
    in_gallery = False
    for line in text.splitlines():
        if line.strip() == "<!-- gallery:start -->":
            _flush(buf)
            in_gallery = True
            _gallery(gallery_items(text))
            continue
        if line.strip() == "<!-- gallery:end -->":
            in_gallery = False
            continue
        if in_gallery:
            continue
        m = IMG_RX.match(line.strip())
        if m:
            _flush(buf)
            path = (GUIDE.parent / m["src"]).resolve()
            if path.exists() and path.is_relative_to(GUIDE.parent):
                st.image(str(path), caption=m["alt"], width=900)
            continue
        buf.append(line)
    _flush(buf)
