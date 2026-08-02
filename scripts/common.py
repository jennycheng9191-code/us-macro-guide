"""共用工具：設定載入、HTTP、序列轉換。"""
from __future__ import annotations

import json
import os
import time
from bisect import bisect_right
from datetime import date, datetime, timedelta
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

MONTHS_BACK = {"yoy": 12, "mom": 1, "mom_diff": 1, "ann3m": 3}
DAYS_BACK = {"yoy": 365, "mom": 30, "mom_diff": 30, "ann3m": 91}
_MONTHLY_FREQ = {"M", "Q", "SA", "A", "BM"}


def _shift_months(iso: str, n: int) -> str:
    y, m, d = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
    m -= n
    while m <= 0:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}-{d:02d}"


def transform(obs: list[dict], display: str, freq: str = "M") -> list[dict]:
    """obs = [{date, value}] 由舊到新。回傳同結構的轉換後序列。

    level     原值
    yoy       年增率 %
    mom       月變動 %
    mom_diff  月變動絕對量
    ann3m     3 個月年化 %
    ma4       4 期移動平均

    ⚠️ 基期一律以「日期」對齊，不可用「往回數 N 筆」。
    官方序列會有缺漏月份（例如 FRED 的 CPIAUCNS 缺 2025-10，
    政府停擺期間未採集），用位置往回數會默默拿錯月份當基期，
    算出來的年增率錯了也不會有人發現。
    """
    if display == "level":
        return [dict(o) for o in obs]

    vals = [o["value"] for o in obs]
    out: list[dict] = []

    if display == "ma4":
        for i, o in enumerate(obs):
            if i >= 3:
                out.append({"date": o["date"], "value": sum(vals[i - 3:i + 1]) / 4})
        return out

    by_date = {o["date"]: o["value"] for o in obs}
    dates = sorted(by_date)
    monthly = freq in _MONTHLY_FREQ

    def base_of(iso: str):
        if monthly:
            return by_date.get(_shift_months(iso, MONTHS_BACK[display]))
        # 日頻/週頻沒有整齊的日期，取「目標日之前最近的一筆」
        target = (datetime.strptime(iso[:10], "%Y-%m-%d").date()
                  - timedelta(days=DAYS_BACK[display])).isoformat()
        i = bisect_right(dates, target) - 1
        return by_date[dates[i]] if i >= 0 else None

    for o in obs:
        prev, cur = base_of(o["date"]), o["value"]
        if prev is None:
            continue
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
