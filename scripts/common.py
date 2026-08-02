"""共用工具：設定載入、HTTP、序列轉換。"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) us-macro-guide/1.0"


def load_env() -> None:
    """本機讀 .env；GitHub Actions 直接用環境變數。"""
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def get_json(url: str, params: dict | None = None, retries: int = 3) -> dict | list:
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30,
                             headers={"User-Agent": UA, "Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        except Exception as e:            # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"取得 JSON 失敗 {url}: {last}")


def get_text(url: str, retries: int = 3) -> str:
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": UA})
            r.raise_for_status()
            return r.text
        except Exception as e:            # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"取得網頁失敗 {url}: {last}")


# ---------------------------------------------------------------- 序列轉換

def _lag_for(freq: str, months: int) -> int:
    """把「幾個月」換算成該頻率下要往回幾個觀測值。"""
    per_month = {"D": 21, "W": 4.345, "BW": 2, "M": 1, "Q": 1 / 3, "SA": 1 / 6, "A": 1 / 12}
    return max(1, round(per_month.get(freq, 1) * months))


def transform(obs: list[dict], display: str, freq: str = "M") -> list[dict]:
    """obs = [{date, value}] 由舊到新。回傳同結構的轉換後序列。

    level     原值
    yoy       年增率 %
    mom       月變動 %
    mom_diff  月變動絕對量
    ann3m     3 個月年化 %
    ma4       4 期移動平均
    """
    vals = [o["value"] for o in obs]
    out: list[dict] = []

    if display == "level":
        return [dict(o) for o in obs]

    if display == "ma4":
        for i, o in enumerate(obs):
            if i < 3:
                continue
            out.append({"date": o["date"], "value": sum(vals[i - 3:i + 1]) / 4})
        return out

    lag = {"yoy": _lag_for(freq, 12), "mom": _lag_for(freq, 1),
           "mom_diff": _lag_for(freq, 1), "ann3m": _lag_for(freq, 3)}[display]

    for i, o in enumerate(obs):
        if i < lag:
            continue
        prev, cur = vals[i - lag], o["value"]
        if display == "mom_diff":
            v = cur - prev
        elif prev == 0:
            continue
        elif display == "ann3m":
            if prev <= 0 or cur <= 0:
                continue
            v = ((cur / prev) ** 4 - 1) * 100      # 3 個月變動年化
        else:
            v = (cur / prev - 1) * 100
        out.append({"date": o["date"], "value": v})
    return out


def days_since(iso: str) -> int:
    try:
        d = datetime.strptime(iso[:10], "%Y-%m-%d").date()
    except ValueError:
        return 9999
    return (date.today() - d).days


# 觀測值的日期是「期別起始日」（6 月 CPI 標成 2026-06-01），
# 直接拿它算距今天數會把正常資料誤判成過期。改從期別結束日起算。
_PERIOD_DAYS = {"D": 0, "W": 6, "BW": 13, "M": 30, "Q": 91, "SA": 182, "A": 364}


def age_from_period_end(iso: str, freq: str = "M") -> int:
    return max(0, days_since(iso) - _PERIOD_DAYS.get(freq, 30))


def read_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return default
    return default


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
