# News Screener — Setup Guide

每天早上一鍵輸出過去 24 小時、與你 watchlist 相關的重要新聞。

---

## 安裝（一次性，5 分鐘）

```bash
# 1. 安裝 Python 套件
pip install -r requirements.txt

# 2. 複製設定檔
cp .env.example .env

# 3. 填入 API keys（用任何文字編輯器開啟 .env）
#    NEWSAPI_KEY   → 去 https://newsapi.org 免費註冊，複製 key 貼上
#    ANTHROPIC_API_KEY → 去 https://console.anthropic.com 取得
```

---

## 每天使用

```bash
# 基本用法：掃描過去 24 小時，輸出到螢幕
python news_screener.py

# 存成 Markdown 檔案
python news_screener.py --out morning_brief.md

# 掃描過去 48 小時（例如週一早上補掃週末）
python news_screener.py --hours 48 --out weekend_brief.md

# 不用 AI 評分（更快，只靠關鍵字比對）
python news_screener.py --no-ai
```

---

## 輸出範例

```
# Daily News Brief  —  2025-07-14 08:02
*Coverage: past 24 hours  |  Watchlist: 60 companies*

**8 companies with news hits:** NVIDIA, TSMC, Broadcom, MediaTek, ...

## NVIDIA  (3 articles)
- [Reuters] NVIDIA beats Q2 earnings, raises full-year guidance
  *2025-07-13 21:00 UTC*
  > Strong data center demand drives upside; positive for supply chain incl. TSMC, SK Hynix.
  NVIDIA Corp reported second-quarter results that topped analyst estimates...

## TSMC  (2 articles)
- [工商時報] 台積電 CoWoS 產能 2026 年擴增 50%
  *2025-07-13 14:30 UTC*
  > Capacity expansion supports AI chip demand visibility; margin-positive.
  ...
```

---

## 自動排程：每天 8:00 自動執行（智慧模式）

腳本 `run_daily.sh` 會自動判斷星期幾：
- **週一** → 抓過去 **72 小時**（補掃週五早上 8 點到週一早上 8 點）
- **週二～週五** → 抓過去 **24 小時**

### macOS / Linux (cron)

```bash
# 1. 給腳本執行權限
chmod +x run_daily.sh

# 2. 開啟 crontab 編輯器
crontab -e

# 3. 加入這行（把路徑換成你實際的資料夾路徑）
0 8 * * 1-5 /Users/yourname/news_screener/run_daily.sh
```

報告會自動存到 `briefs/brief_YYYY-MM-DD.md`。

### Windows (工作排程器)

1. 搜尋「工作排程器」→「建立基本工作」
2. 觸發程序：每天 08:00，重複週一到週五
3. 動作：執行 `python`，引數 `news_screener.py --hours 24 --out briefs/brief_%date%.md`

---

## 新聞來源

| 來源 | 類型 | 說明 |
|------|------|------|
| Reuters Tech/Business | RSS | 即時，英文 |
| WSJ Tech/Markets | RSS | 英文 |
| Yahoo Finance | RSS | 主要 US ticker 即時報價新聞 |
| 工商時報 產業/科技 | RSS | 繁中，台股 |
| 鉅亨網 台股 | RSS | 繁中，台股 |
| 經濟日報 科技/產業 | RSS | 繁中，台股 |
| NewsAPI | API | 100+ 英文媒體聚合，含 Bloomberg 標題 |

---

## 客製化

### 新增/移除股票
開啟 `news_screener.py`，找到 `WATCHLIST` 字典直接修改：

```python
"新公司名稱": ["English name", "中文名稱", "TICKER"],
```

### 新增 RSS 來源
在 `RSS_FEEDS` 清單加入任何 RSS URL 即可。
