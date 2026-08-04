# 美國總經指標手冊（自動更新版）

49 個美國總經指標的參考手冊，數值每天由 GitHub Actions 自動抓取官方來源更新。
前身是每次都要重跑 skill 才會更新的靜態 HTML。

## 這份東西怎麼運作

```
GitHub Actions（每天台北 08:00）
   └─ scripts/build.py
        ├─ 抓取     FRED / BLS / Treasury / 官方網頁 / 官方新聞稿 / Cleveland Fed
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
| FRED API | 32 | 需要免費金鑰，序列代號皆已逐一驗證（含 ADP 官方序列） |
| ISM 官方新聞稿（PR Newswire） | 6 | ISM×6，官方原文全文，分項數字齊全 |
| Treasury API | 4 | TGA / Bill 占比 / MTS / 拍賣結果，免金鑰 |
| 官方網頁解析 | 2 | Conference Board、NAHB |
| Cleveland Fed 官方 JSON | 2 | CPI / PCE 通膨即時預測，免金鑰 |
| NY Fed SCE 資料檔 | 1 | xlsx |
| 衍生計算 | 1 | SOFR − IORB |
| 人工 | 1 | QRA（敘述性內容） |

新聞抓取（`scripts/sources/news.py`）現在只作為 ADP 的備援，沒有任何卡片以它為主要來源。

被封鎖而無法直接抓的來源（已實測）：
ISM 官網為 reCAPTCHA 牆（含 `/ism-pmi-reports/` 等所有路徑，一律轉址到 SSO 登入頁）、
ADP 官網為 JS 外殼、S&P Global PMI 403、Reuters 與 MarketWatch 401、
AP News 已改為前端渲染（hub 頁抓不到任何文章連結）。
ADP 的月報在 PR Newswire 上只零星出現（發布者頁穩定發的是每週初值），故改走 FRED。

### ISM 為什麼改抓 PR Newswire

2026-08-03 的 7 月製造業 ISM 是 CNBC＋AP 雙來源機制的第一次實戰，結果六張卡全部未取得：
AP 那一路已完全失效（永遠湊不到雙來源），CNBC 雖有報導但寫的是「a 55.6 reading」，
不在原本的動詞清單裡；且記者本來就不會逐項報新訂單、就業這些分項數字。

ISM 每月的 Report On Business **官方新聞稿全文**會同步發到 PR Newswire，免費、無驗證碼、
句式每月固定、分項齊全，且總指數的歷史值直接寫在網址裡
（`manufacturing-pmi-at-55-6-july-2026-...`），抓 24 期歷史完全不需下載內文。
這是第一手官方原文，比兩個二手轉述更可靠，因此不受雙來源交叉驗證關卡限制。

## 方向箭頭與債市多空

箭頭**一律誠實表示數值本身的升降**，債市多空由顏色與標籤承載。兩者刻意分開：
49 張卡的語義方向並不一致（CPI 升是利空、失業率升是利多），
若把箭頭本身翻過來，看到 ▼ 會誤以為數值下降。

| mapping 的 `bond_dir` | 意義 | 呈現 |
| :-- | :-- | :-- |
| `1` | 值上升 → 利空債市（殖利率上行壓力） | 綠色 ＋「利空債市」標籤 |
| `-1` | 值上升 → 利多債市 | 紅色 ＋「利多債市」標籤 |
| 不設 | 語義不明確 | 中性灰，不加標籤 |

配色比照台股「紅漲綠跌」，但**以債券價格為準**：利多債市＝債價上漲＝紅，
利空債市＝殖利率上行＝債價下跌＝綠。跟看殖利率走勢的直覺相反，圖例已標明。

目前 35 張標利空向、4 張標利多向（失業率、初領失業金、MTS 財政收支、信用 OAS）、
10 張留白。**留白是刻意的**：TGA、Bill 占比、ON RRP、NFCI、準備金、SOFR-IORB
這類卡的多空取決於當下情境（例如 TGA 上升在不同時期對流動性的含義相反），
勞動參與率與 30 年房貸利率同理。寧可沒有，不可亂寫。

要改某張卡的方向，只需在 `data/mapping.json` 加減 `"bond_dir"` 鍵，前端不用動。

⚠️ `bond_dir`（mapping，數字方向）與 `bond`（indicators.json，「債市含義」的敘述文字）
是**兩個不同的東西**，前端一個讀 `c.bond_dir` 一個讀 `d.bond`。當初就是為了避免混淆
才把數字那個改名成 `bond_dir`，不要改回去。

## 燈號

| 燈號 | 意義 |
| :-- | :-- |
| 🟢 | 資料在正常發布間隔內，且通過三道關卡 |
| 🟡 | 資料過期、或未通過驗證而沿用前值——**需要你確認** |
| ⚪ | 未取得——卡片不會顯示任何數值，被關卡擋下的值一律清空不外流 |

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
| `data/indicators.json` | 49 卡知識層（解讀方法論、債市含義、關聯指標）——幾乎不會變 |
| `data/mapping.json` | 每張卡的資料來源、序列代號、單位、合理區間、適用規則 |
| `data/latest.json` | 每日產出的數值層，網頁唯一讀取的檔案 |
| `docs/mapping-review.md` | 47 卡來源對照清單（2026-08-02 建立，未含後來新增的 Cleveland Fed 兩張），供抽查 |
| `scripts/test_news_extractor.py` | 新聞抽取器回歸測試，改正則後務必執行 |
| `scripts/test_prnewswire.py` | ISM 新聞稿抽取器回歸測試；加 `--live` 會用「前後期互證」驗完整 24 期 |
| `scripts/test_clevelandfed.py` | 通膨即時預測抽取器回歸測試（事件標記濾除、選月規則） |

## 維護時的注意事項

- 調整 `scripts/sources/news.py` 的正則後，**一定要跑回歸測試**。判準不是「盡量抓到」而是「絕不抓錯」——抓不到會亮黃燈由人補，抓錯了不會有人發現。
- 新聞與網頁解析的中間段一律用 `[\s\S]` 而非 `[^.]`。新聞句子常夾帶「down from 49.5」這種帶小數點的數字，用 `[^.]` 會提前截斷。
- FRED 觀測值的日期是**期別起始日**（6 月 CPI 標成 `2026-06-01`），算新鮮度時必須從期別結束日起算，否則正常資料會被誤判成過期。
- ISM 新聞稿的分項小標寫成 `Employment Index at 51.2%`（用 `%` 符號），內文則寫 `51.2 percent`。抽取器兩種都要認——只認 `percent` 會略過小標、讓取值視窗滑進下一句，把服務業就業抓成 Services PMI 的數字。
- `scale`（單位換算）必須用**實際取數的那份 mapping**。走備援時來源的原始單位不同，拿主要來源的倍率去乘備援的值會差好幾個數量級。`build.dispatch` 已在各自的來源上套用。
- ISM 每年 1 月會完成**季調因子的年度修正**，1 月號引述的 12 月值與 12 月當初公布的不同（例：47.7 → 47.4）。歷史序列在 12 月／1 月交界本來就會混到兩個 vintage，`test_prnewswire.py --live` 已把這個邊界排除，不是錯誤。
- Cleveland Fed 的 `categories` 裡混了事件標記（`CPI Jun`、`PCE Jun`，圖上標示前期公布日的垂直線），**不占資料點**：27 個標籤對 25 筆值。必須把非日期標籤整個濾掉再對齊，留空位會讓整條序列錯位。
- Cleveland Fed 的目標月只能取「檔尾**連續**還沒有 Actual 的那一段」。歷史區間中間也有 Actual 空缺（2013-07 資料缺漏、2025-10 政府停擺期間未採集 CPI），從頭掃第一個空的會選到十幾年前。CPI 與 PCE 公布時程不同，各自用自己的 Actual 序列判斷。
