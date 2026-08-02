# 美國總經指標手冊（自動更新版）

47 個美國總經指標的參考手冊，數值每天由 GitHub Actions 自動抓取官方來源更新。
前身是每次都要重跑 skill 才會更新的靜態 HTML。

## 這份東西怎麼運作

```
GitHub Actions（每天台北 08:00）
   └─ scripts/build.py
        ├─ 抓取     FRED / BLS / Treasury / 官方網頁 / 新聞
        ├─ 三道關卡  合理範圍、變動幅度、雙來源交叉驗證
        ├─ 規則判讀  榮枯線、Sahm Rule、3個月年化、V/U 比、百分位…
        └─ 寫出     data/latest.json
                        └─ index.html 讀取後渲染（純靜態，無後端）
```

**核心設計原則：抓取失敗時保留前值並亮黃燈，絕不顯示未經驗證的數字。**
對交易用途而言，沒有更新遠比更新成錯的安全。

## 資料來源分布

| 來源 | 卡數 | 備註 |
| :-- | --: | :-- |
| FRED API | 31 | 需要免費金鑰，序列代號皆已逐一驗證 |
| 新聞雙來源（CNBC＋AP） | 7 | ISM×6 ＋ ADP，官網封鎖故走此路 |
| Treasury API | 4 | TGA / Bill 占比 / MTS / 拍賣結果，免金鑰 |
| 官方網頁解析 | 2 | Conference Board、NAHB |
| NY Fed SCE 資料檔 | 1 | xlsx |
| 衍生計算 | 1 | SOFR − IORB |
| 人工 | 1 | QRA（敘述性內容） |

被封鎖而無法直接抓的來源（已實測）：
ISM 官網為 reCAPTCHA 牆、ADP 官網為 JS 外殼、S&P Global PMI 403、Reuters 與 MarketWatch 401。

## 燈號

| 燈號 | 意義 |
| :-- | :-- |
| 🟢 | 資料在正常發布間隔內，且通過三道關卡 |
| 🟡 | 資料過期、或未通過驗證而沿用前值——**需要你確認** |
| ⚪ | 未取得 |

## 本機執行

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env          # 填入 FRED_API_KEY
.venv/Scripts/python scripts/build.py
.venv/Scripts/python -m http.server 8899    # 開 http://127.0.0.1:8899
```

## 人工補值

ISM 亮黃燈或未取得時，把數字寫進 `data/manual.json`：

```json
{
  "ism_manufacturing_pmi": {
    "value": 48.2,
    "asof": "2026-07-01",
    "by": "Jenny",
    "at": "2026-08-03"
  }
}
```

人工值的優先序最高，會蓋過任何自動抓取結果（對應原本「TradingView 截圖數值優先於一切抓取」的規則）。

## 目錄

| 路徑 | 用途 |
| :-- | :-- |
| `data/indicators.json` | 47 卡知識層（解讀方法論、債市含義、關聯指標）——幾乎不會變 |
| `data/mapping.json` | 每張卡的資料來源、序列代號、單位、合理區間、適用規則 |
| `data/latest.json` | 每日產出的數值層，網頁唯一讀取的檔案 |
| `docs/mapping-review.md` | 47 卡來源對照清單，供抽查 |
| `scripts/test_news_extractor.py` | 新聞抽取器回歸測試，改正則後務必執行 |

## 維護時的注意事項

- 調整 `scripts/sources/news.py` 的正則後，**一定要跑回歸測試**。判準不是「盡量抓到」而是「絕不抓錯」——抓不到會亮黃燈由人補，抓錯了不會有人發現。
- 新聞與網頁解析的中間段一律用 `[\s\S]` 而非 `[^.]`。新聞句子常夾帶「down from 49.5」這種帶小數點的數字，用 `[^.]` 會提前截斷。
- FRED 觀測值的日期是**期別起始日**（6 月 CPI 標成 `2026-06-01`），算新鮮度時必須從期別結束日起算，否則正常資料會被誤判成過期。
