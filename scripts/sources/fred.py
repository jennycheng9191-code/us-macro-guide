"""FRED API 抓取模組（31 張卡的主力來源，另供衍生計算使用）。"""
from __future__ import annotations

import os

from common import get_json, transform

BASE = "https://api.stlouisfed.org/fred"
_meta_cache: dict[str, dict] = {}
_obs_cache: dict[str, list[dict]] = {}


def _key() -> str:
    k = os.environ.get("FRED_API_KEY", "").strip()
    if not k:
        raise RuntimeError("缺少 FRED_API_KEY")
    return k


def meta(series_id: str) -> dict:
    if series_id not in _meta_cache:
        d = get_json(f"{BASE}/series",
                     {"series_id": series_id, "file_type": "json", "api_key": _key()})
        _meta_cache[series_id] = d["seriess"][0]
    return _meta_cache[series_id]


def observations(series_id: str, limit: int = 140) -> list[dict]:
    """回傳由舊到新的 [{date, value}]，已剔除 FRED 的缺值符號 '.'。"""
    if series_id in _obs_cache:
        return _obs_cache[series_id]
    d = get_json(f"{BASE}/series/observations",
                 {"series_id": series_id, "file_type": "json", "api_key": _key(),
                  "sort_order": "desc", "limit": limit})
    obs = []
    for o in d.get("observations", []):
        if o["value"] in (".", "", None):
            continue
        obs.append({"date": o["date"], "value": float(o["value"])})
    obs.reverse()
    _obs_cache[series_id] = obs
    return obs


def _series_result(series_id: str, display: str) -> dict:
    obs = observations(series_id)
    if not obs:
        return {"ok": False, "reason": f"{series_id} 無可用觀測值"}
    freq = meta(series_id).get("frequency_short", "M")
    ser = transform(obs, display, freq)
    if not ser:
        return {"ok": False, "reason": f"{series_id} 資料長度不足以計算 {display}"}
    return {
        "ok": True,
        "value": ser[-1]["value"],
        "asof": ser[-1]["date"],
        "history": ser[-24:],
        "raw_latest": obs[-1]["value"],
        "freq": freq,
        "source_label": f"FRED {series_id}",
    }


def fetch(card_id: str, m: dict) -> dict:
    res = _series_result(m["series"], m.get("display", "level"))
    if not res["ok"]:
        return res

    # 附帶序列（子項 / 對照組）
    extras: dict[str, float] = {}
    for label, sid in (m.get("extras") or {}).items():
        try:
            o = observations(sid)
            if o:
                extras[label] = o[-1]["value"]
        except Exception as e:                      # noqa: BLE001
            extras[label] = None
    res["extras"] = extras

    # 額外的呈現形式（例如同時給 mom 與 3 個月年化）
    also: dict[str, float] = {}
    for form in m.get("also", []):
        if form.startswith("spread_vs_"):
            other = form.replace("spread_vs_", "")
            try:
                o = observations(other)
                if o:
                    also[f"利差 vs {other}"] = res["raw_latest"] - o[-1]["value"]
            except Exception:                       # noqa: BLE001
                pass
        elif form == "hy_ig_ratio":
            try:
                hy = observations("BAMLH0A0HYM2")
                if hy:
                    also["HY/IG 比"] = hy[-1]["value"] / res["raw_latest"]
            except Exception:                       # noqa: BLE001
                pass
        else:
            r = _series_result(m["series"], form)
            if r["ok"]:
                also[form] = r["value"]
    res["also"] = also
    return res


def fetch_derived(card_id: str, m: dict) -> dict:
    """目前只有 SOFR - IORB 一張卡，單位換算為 bp。"""
    a, b = m["inputs"]
    oa, ob = observations(a), observations(b)
    if not oa or not ob:
        return {"ok": False, "reason": f"{a} 或 {b} 無資料"}

    # 兩個日頻序列的日期對齊後相減
    mb = {o["date"]: o["value"] for o in ob}
    hist = [{"date": o["date"], "value": (o["value"] - mb[o["date"]]) * 100}
            for o in oa if o["date"] in mb]
    if not hist:
        return {"ok": False, "reason": f"{a} 與 {b} 沒有共同日期"}
    return {
        "ok": True,
        "value": hist[-1]["value"],
        "asof": hist[-1]["date"],
        "history": hist[-24:],
        "raw_latest": hist[-1]["value"],
        "freq": "D",
        "extras": {a: oa[-1]["value"], b: mb[hist[-1]["date"]]},
        "also": {},
        "source_label": f"FRED {a} − {b}",
    }
