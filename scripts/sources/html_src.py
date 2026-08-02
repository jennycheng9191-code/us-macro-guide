"""解析官方網頁 HTML：Conference Board 消費者信心、NAHB 建商信心。

兩者的數字都直接寫在新聞稿段落裡（2026-08-02 實測），
所以先把 HTML 標籤剝掉再用嚴格的語境正則抓，比解析 DOM 穩定。
"""
from __future__ import annotations

import re

from common import get_text

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"], 1)}


def _plain(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|svg)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = (html.replace("&nbsp;", " ").replace("&mdash;", "—").replace("&reg;", "")
                .replace("&rsquo;", "'").replace("&ldquo;", '"').replace("&rdquo;", '"')
                .replace("&amp;", "&").replace("&ndash;", "–"))
    return re.sub(r"\s+", " ", html)


def _month_to_date(name: str, year: int | None = None) -> str:
    from datetime import date
    mi = MONTHS.get(name.capitalize())
    if not mi:
        return ""
    today = date.today()
    y = year or today.year
    if year is None and mi > today.month:       # 例如 12 月的報告在 1 月才讀到
        y -= 1
    return f"{y}-{mi:02d}-01"


def conference_board(m: dict) -> dict:
    txt = _plain(get_text(m["url"]))

    # 注意：敘述句裡含有「decreased by 1.4 points to 90.8」這種帶小數點的數字，
    # 所以中間段不能用 [^.]，必須用 [\s\S] 並靠 (1985=100) 這個強錨點限制範圍。
    main = re.search(
        r"Consumer Confidence Index[\s\S]{0,160}?\b(?:to|at)\s+([0-9]{2,3}\.[0-9])\s*\(1985=100\)\s*in\s+([A-Za-z]+)",
        txt)
    if not main:
        return {"ok": False, "reason": "Conference Board 頁面未比對到信心指數敘述句"}
    value, month = float(main.group(1)), main.group(2)

    def grab(label: str) -> float | None:
        mm = re.search(label + r"[\s\S]{0,240}?\b(?:to|at)\s+([0-9]{2,3}\.[0-9])", txt)
        return float(mm.group(1)) if mm else None

    return {"ok": True, "value": value, "asof": _month_to_date(month),
            "asof_label": f"{month}", "history": [],
            "raw_latest": value, "freq": "M",
            "extras": {"現況指數": grab("Present Situation Index"),
                       "預期指數": grab("Expectations Index")},
            "also": {}, "source_label": "Conference Board 官網新聞稿"}


def nahb(m: dict) -> dict:
    txt = _plain(get_text(m["url"]))

    period = re.search(r"HMI Key Findings:\s*([A-Za-z]+)\s+(\d{4})", txt)
    val = re.search(
        r"Builder confidence[\s\S]{0,180}?\b(?:to|at)\s+(\d{1,3})\s+in\s+[A-Z][a-z]+",
        txt)
    if not (period and val):
        return {"ok": False, "reason": "NAHB 頁面未比對到 HMI Key Findings 敘述句"}

    month, year = period.group(1), int(period.group(2))
    return {"ok": True, "value": float(val.group(1)),
            "asof": _month_to_date(month, year), "asof_label": f"{year} {month}",
            "history": [], "raw_latest": float(val.group(1)), "freq": "M",
            "extras": {}, "also": {}, "source_label": "NAHB 官網 HMI 頁"}


HANDLERS = {"confidence_index": conference_board, "hmi_key_findings": nahb}


def fetch(card_id: str, m: dict) -> dict:
    h = HANDLERS.get(m.get("pattern", ""))
    if not h:
        return {"ok": False, "reason": f"未知的 HTML 解析型別 {m.get('pattern')}"}
    return h(m)
