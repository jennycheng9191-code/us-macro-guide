"""組裝 data/latest.json —— 網頁唯一讀取的資料檔。

流程：逐卡抓取 → 三道關卡驗證 → 規則判讀 → 寫檔。
任何一張卡失敗都不中斷整體流程，改為沿用上一版的值並亮燈。
"""
from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "sources")]

from common import DATA, load_env, read_json, write_json   # noqa: E402
import rules                                               # noqa: E402
import validate                                            # noqa: E402
from sources import fred, html_src, news, nyfed, prnewswire, treasury, umich   # noqa: E402

TPE = timezone(timedelta(hours=8))


def _fetch_one(card_id: str, m: dict, ctx: dict) -> dict:
    src = m["source"]
    if src == "fred":
        return fred.fetch(card_id, m)
    if src == "derived":
        return fred.fetch_derived(card_id, m)
    if src == "treasury":
        return treasury.fetch(card_id, m)
    if src == "html":
        return html_src.fetch(card_id, m)
    if src == "nyfed_sce":
        return nyfed.fetch(card_id, m)
    if src == "umich":
        return umich.fetch(card_id, m)
    if src == "prnewswire":
        return prnewswire.fetch(card_id, m)
    if src == "news":
        return news.fetch(card_id, m, ctx.setdefault("news_urls", news._article_urls()))
    if src == "manual":
        return {"ok": False, "reason": "敘述性內容，依行事曆人工更新"}
    return {"ok": False, "reason": f"未知來源型別 {src}"}


def dispatch(card_id: str, m: dict, ctx: dict) -> dict:
    """主要來源失敗時，改試 mapping 裡宣告的備援來源。

    備援結果會標上 source_kind，validate 才知道要用備援來源的關卡規則
    （例如新聞來源仍須雙來源交叉驗證，不會因為掛在官方卡下就免驗）。
    """
    res = _fetch_one(card_id, m, ctx)
    fb = m.get("fallback")
    if res.get("ok") or not fb:
        return res

    try:
        alt = _fetch_one(card_id, {**m, **fb}, ctx)
    except Exception as e:                                      # noqa: BLE001
        print(f"  ! {card_id} 備援來源也失敗：{e}", file=sys.stderr)
        return res
    if not alt.get("ok"):
        return res

    alt["source_kind"] = fb["source"]
    alt["source_label"] = f"{alt.get('source_label') or fb['source']}（備援）"
    alt["fallback_note"] = f"主要來源未取得（{res.get('reason', '—')}），改用備援來源"
    return alt


def fmt(value, m: dict) -> str:
    if value is None:
        return "—"
    d = m.get("decimals", 1)
    unit = m.get("unit", "")
    s = f"{value:,.{d}f}"
    return f"{s}{unit}" if unit and unit != "%" else (f"{s}%" if unit == "%" else s)


def main() -> int:
    load_env()
    indicators = read_json(DATA / "indicators.json", [])
    mapping = read_json(DATA / "mapping.json", {})
    mapping.pop("_doc", None)
    manual = read_json(DATA / "manual.json", {})
    previous = read_json(DATA / "latest.json", {}).get("cards", {})

    ctx: dict = {}
    cards: dict[str, dict] = {}
    tally = {"green": 0, "yellow": 0, "gray": 0}

    for card in indicators:
        cid = card["id"]
        m = mapping.get(cid)
        if not m:
            continue

        try:
            res = dispatch(cid, m, ctx)
        except Exception as e:                                  # noqa: BLE001
            res = {"ok": False, "reason": f"抓取例外：{e}"}
            print(f"  ! {card['n']}: {e}", file=sys.stderr)
            traceback.print_exc(limit=1, file=sys.stderr)

        # 單位換算（例如 FRED 的百萬美元 → 十億美元）。
        # 必須在驗證之前套用，sanity 區間才會跟顯示單位一致。
        if (sc := m.get("scale")) and res.get("ok"):
            if res.get("value") is not None:
                res["value"] *= sc
            if res.get("raw_latest") is not None:
                res["raw_latest"] *= sc
            res["history"] = [{"date": h["date"], "value": h["value"] * sc}
                              for h in res.get("history", [])]

        verdict = validate.check(res, m)
        status, notes = verdict["status"], list(verdict["notes"])

        # 走備援來源代表主要來源當下是壞的——即使數字通過關卡也要讓你看得見
        if res.get("fallback_note"):
            notes.insert(0, res["fallback_note"])
            status = "yellow" if status == "green" else status

        # 人工確認值最優先（你貼的數字或 TradingView 截圖）
        if cid in manual:
            man = manual[cid]
            res = {"ok": True, "value": man.get("value"), "asof": man.get("asof", ""),
                   "history": res.get("history", []) if res.get("ok") else [],
                   "extras": man.get("extras", {}), "also": {},
                   "source_label": "人工輸入", "raw_latest": man.get("value")}
            status, notes = "green", [f"人工確認值（{man.get('by', 'Jenny')} 於 {man.get('at', '—')}）"]

        # 抓不到就沿用上一版，並明確標示
        elif status == "gray" and cid in previous and previous[cid].get("value") is not None:
            old = previous[cid]
            notes.append(f"本次未取得，沿用 {old.get('asof', '—')} 的前值")
            res = {"ok": True, "value": old["value"], "asof": old.get("asof", ""),
                   "history": old.get("history", []), "extras": old.get("extras", {}),
                   "also": old.get("also", {}), "source_label": old.get("source_label", ""),
                   "raw_latest": old.get("value")}
            status = "yellow"

        # GDPNow 的觀測日期是「預測的那一季」，不是資料期別，標清楚免得誤讀
        if m.get("label_as") == "quarter" and res.get("asof"):
            y, mo = res["asof"][:4], int(res["asof"][5:7])
            res["value_label"] = f"{y} Q{(mo - 1) // 3 + 1} 預測值"

        # 灰燈代表這個值不可信（沒抓到，或沒過關卡 1）。值必須清掉——
        # 留著的話前端只要有一處照著 value 渲染，就會把被擋下的錯誤數字顯示出來。
        if status == "gray":
            res = {"ok": False, "asof": "", "history": [], "extras": {}, "also": {},
                   "source_label": res.get("source_label", "")}

        note = rules.build_note(res, m) if res.get("ok") else ""
        tally[status] = tally.get(status, 0) + 1

        cards[cid] = {
            "value": res.get("value"),
            "value_fmt": fmt(res.get("value"), m) if res.get("ok") else "—",
            "value_label": res.get("value_label", ""),
            "asof": res.get("asof", ""),
            "asof_label": res.get("asof_label", ""),
            "age_days": res.get("age_days"),
            "history": res.get("history", []),
            "extras": {k: v for k, v in (res.get("extras") or {}).items() if v is not None},
            "also": res.get("also", {}),
            "status": status,
            "notes": notes,
            "note": note,
            "source_label": res.get("source_label", ""),
            "unit": m.get("unit", ""),
            "display": m.get("display", "level"),
        }
        flag = {"green": "OK", "yellow": "!!", "gray": "--"}[status]
        print(f"  [{flag}] {card['n']:<22} {cards[cid]['value_fmt']:>14}  {res.get('asof', '')}")

    out = {
        "build_time": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"),
        "summary": tally,
        "cards": cards,
    }
    write_json(DATA / "latest.json", out)
    print(f"\n完成：綠燈 {tally['green']} / 黃燈 {tally['yellow']} / 未取得 {tally['gray']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
