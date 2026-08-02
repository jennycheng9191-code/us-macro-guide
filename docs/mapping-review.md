# 47 卡資料來源對照清單

> 產生日期：2026-08-02　所有 FRED 序列代號已逐一透過 API 驗證存在且仍在更新。
> **抽查重點**：`display` 欄決定卡片顯示的是原值還是年增率——這是最容易和舊版手冊對不起來的地方。

| # | 指標 | 面向 | 來源 | 序列/端點 | 顯示 | 附帶序列 | 備註 |
|--:|:--|:--|:--|:--|:--|:--|:--|
| 1 | CPI 總指數 | 通膨 | fred | CPIAUCSL | yoy |  |  |
| 2 | 核心CPI | 通膨 | fred | CPILFESL | yoy |  |  |
| 3 | Super Core(核心服務ex住房) | 通膨 | fred | CUSR0000SASL2RS | yoy |  | FRED 官方『服務業扣除房租』序列，即 Super Core 的標準代理 |
| 4 | OER / 房租分項 | 通膨·房市 | fred | CUSR0000SEHC | yoy |  |  |
| 5 | PCE / 核心PCE物價 | 通膨 | fred | PCEPILFE | yoy | 總指數=PCEPI |  |
| 6 | Trimmed Mean PCE | 通膨 | fred | PCETRIM12M159SFRBDAL | level | 單月年化=PCETRIM1M158SFRBDAL |  |
| 7 | PPI 生產者物價 | 通膨 | fred | PPIFIS | yoy |  |  |
| 8 | 5y5y 通膨預期(遠期損益兩平) | 通膨·金融 | fred | T5YIFR | level |  |  |
| 9 | NY Fed 消費者通膨預期 | 通膨 | nyfed_sce | https://www.newyorkfed.org/medi... | level |  |  |
| 10 | 密大通膨預期 | 通膨·信心 | fred | MICH | level |  | MICH 為 1 年期預期；5–10 年期 FRED 無對應序列 |
| 11 | 非農就業 NFP | 勞動 | fred | PAYEMS | mom_diff |  |  |
| 12 | 失業率 | 勞動 | fred | UNRATE | level |  |  |
| 13 | 勞動參與率 | 勞動 | fred | CIVPART | level | 25-54歲=LNS11300060 |  |
| 14 | 平均時薪 AHE | 勞動·薪資 | fred | CES0500000003 | yoy |  |  |
| 15 | JOLTS 職缺 | 勞動 | fred | JTSJOL | level | 離職率=JTSQUR、失業人數=UNEMPLOY | JOLTS 本身滯後約 2 個月，stale_days 已放寬 |
| 16 | 初領失業金 | 勞動 | fred | ICSA | level | 續領=CCSA |  |
| 17 | ADP 民間就業 | 勞動 | news | ADP private payrolls / ADP empl... | mom_diff |  | 官網為 JS 外殼無法解析；改走新聞雙來源，FRED 週頻序列備援 |
| 18 | ISM製造業就業分項 | 勞動·經濟活動 | news | ISM manufacturing employment | level |  |  |
| 19 | ISM服務業就業分項 | 勞動·經濟活動 | news | ISM services employment | level |  |  |
| 20 | ECI 僱傭成本指數 | 薪資 | fred | ECIALLCIV | yoy | 民間工資薪金=ECIWAG |  |
| 21 | Atlanta Fed 薪資追蹤 | 薪資 | fred | FRBATLWGT3MMAUMHWGO | level |  |  |
| 22 | ISM製造業PMI | 經濟活動 | news | ISM manufacturing PMI / manufac... | level |  |  |
| 23 | ISM製造新訂單 | 經濟活動 | news | ISM manufacturing new orders | level |  |  |
| 24 | ISM製造物價分項 | 經濟活動·通膨 | news | ISM manufacturing prices paid /... | level |  |  |
| 25 | ISM服務業PMI | 經濟活動 | news | ISM services PMI / services PMI | level |  |  |
| 26 | 零售銷售 | 經濟活動 | fred | RSAFS | yoy | 扣除餐飲=RSXFS |  |
| 27 | 工業生產 | 經濟活動 | fred | INDPRO | yoy | 產能利用率=TCU |  |
| 28 | GDPNow | 經濟活動 | fred | GDPNOW | level |  |  |
| 29 | 耐久財訂單 | 經濟活動 | fred | DGORDER | yoy | 核心資本財=NEWORDER |  |
| 30 | 密大消費者信心 | 信心 | fred | UMCSENT | level |  |  |
| 31 | CB 消費者信心 | 信心·勞動 | html | https://www.conference-board.or... | level |  | 2026-08-02 實測：數字直接寫在 HTML 原文段落中 |
| 32 | NAHB 建商信心 | 房市 | html | https://www.nahb.org/news-and-e... | level |  | 2026-08-02 實測：HMI Key Findings 段落含數字，另附 .xls 歷史檔 |
| 33 | 新屋開工 / 建照 | 房市 | fred | HOUST | level | 建照=PERMIT、單戶開工=HOUST1F |  |
| 34 | 成屋銷售 | 房市 | fred | EXHOSLUSM495S | level |  |  |
| 35 | 新屋銷售 | 房市 | fred | HSN1F | level |  |  |
| 36 | Case-Shiller 房價 | 房市 | fred | SPCS20RSA | yoy | 全國指數=CSUSHPINSA | 本身滯後 2 個月；FRED 已更名為 S&P Cotality Case-Shiller |
| 37 | 30年期房貸利率 | 房市·金融 | fred | MORTGAGE30US | level | 10Y公債=DGS10 |  |
| 38 | QRA 季度再融資 | 財政 | manual | https://home.treasury.gov/polic... | text |  | 敘述性內容無法量化自動抓；依行事曆亮黃燈提醒 |
| 39 | 附息債拍賣結果 | 財政 | treasury | treasurydirect_auctions | table |  | 2026-08-02 實測 API 正常回傳 JSON |
| 40 | TGA 財政部現金餘額 | 財政·金融 | treasury | fiscaldata_dts | level |  | 2026-08-02 實測抓到 7/30 = 9,704 億美元 |
| 41 | Bill 占比 | 財政 | treasury | fiscaldata_mspd | pct |  |  |
| 42 | MTS 月度財政收支 | 財政 | treasury | fiscaldata_mts | level |  | 欄位名需於實作時查 API 文件確認 |
| 43 | NFCI 金融條件指數 | 金融 | fred | NFCI | level | 調整版=ANFCI |  |
| 44 | SOFR-IORB 利差 | 金融 | derived | SOFR - IORB | level |  |  |
| 45 | ON RRP 餘額 | 金融 | fred | RRPONTSYD | level |  |  |
| 46 | 銀行準備金餘額 | 金融 | fred | WRESBAL | level |  |  |
| 47 | 信用OAS(IG/HY) | 金融 | fred | BAMLC0A0CM | level | HY=BAMLH0A0HYM2 |  |
