#!/usr/bin/env python3
import argparse, os, sys, time, json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import feedparser, requests
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# WATCHLIST  (display name → search keywords)
# ─────────────────────────────────────────────
WATCHLIST = {
    "TSMC":              ["TSMC", "Taiwan Semiconductor", "台積電", "TSM"],
    "UMC":               ["UMC", "United Microelectronics", "聯電"],
    "MediaTek":          ["MediaTek", "聯發科", "MTK"],
    "ASPEED Tech":       ["ASPEED", "信驊"],
    "ASE Technology":    ["ASE Technology", "ASE Group", "日月光", "ASX"],
    "Chroma ATE":        ["Chroma", "致茂"],
    "Unimicron":         ["Unimicron", "欣興"],
    "Nan Ya PCB":        ["Nan Ya PCB", "Nan Ya Printed", "南亞電路板"],
    "Kinsus":            ["Kinsus", "景碩"],
    "Gold Circuit":      ["Gold Circuit", "GCE"],
    "Elite Material":    ["Elite Material", "EMC"],
    "Tripod Tech":       ["Tripod Technology", "健鼎科技"],
    "Taiwan Union":      ["Taiwan Union", "台燿"],
    "Hon Hai (Foxconn)": ["Hon Hai", "Foxconn", "鴻海", "富士康"],
    "Quanta Computer":   ["Quanta Computer", "廣達"],
    "Inventec":          ["Inventec", "英業達"],
    "Wistron":           ["Wistron", "緯創"],
    "Wiwynn":            ["Wiwynn", "緯穎"],
    "Pegatron":          ["Pegatron", "和碩"],
    "Compal":            ["Compal", "仁寶"],
    "Celestica":         ["Celestica", "CLS"],
    "Flex Ltd":          ["Flex Ltd", "Flextronics"],
    "Jabil":             ["Jabil"],
    "ASUSTeK":           ["ASUS", "ASUSTeK", "華碩"],
    "Acer":              ["Acer", "宏碁"],
    "Delta Electronics": ["Delta Electronics", "台達電"],
    "Lite-On":           ["Lite-On", "光寶"],
    "Hon Precision":     ["Hon Precision", "鴻準"],
    "Lotes":             ["Lotes", "正崴"],
    "BizLink":           ["BizLink", "彼洋"],
    "Jentech":           ["Jentech", "健策"],
    "Accton":            ["Accton", "智邦"],
    "Auras Technology":  ["Auras", "雙鴻"],
    "Asia Vital":        ["Asia Vital", "AVC", "建準"],
    "NVIDIA":            ["NVIDIA", "NVDA", "Nvidia"],
    "Intel":             ["Intel", "INTC"],
    "Broadcom":          ["Broadcom", "AVGO"],
    "AMD":               ["AMD", "Advanced Micro Devices"],
    "Marvell":           ["Marvell Technology", "Marvell", "MRVL"],
    "Qualcomm":          ["Qualcomm", "QCOM"],
    "Astera Labs":       ["Astera Labs", "ALAB"],
    "Credo Technology":  ["Credo Technology", "CRDO"],
    "Micron":            ["Micron Technology", "Micron", "MU"],
    "Lumentum":          ["Lumentum", "LITE"],
    "Coherent":          ["Coherent Corp", "COHR"],
    "Fabrinet":          ["Fabrinet", "FN"],
    "Apple":             ["Apple", "AAPL"],
    "Microsoft":         ["Microsoft", "MSFT"],
    "Amazon (AWS)":      ["Amazon", "AWS", "AMZN"],
    "Alphabet (Google)": ["Alphabet", "Google", "GOOGL"],
    "Meta":              ["Meta Platforms", "Meta", "Facebook", "META"],
    "Super Micro":       ["Super Micro", "Supermicro", "SMCI"],
    "Dell Technologies": ["Dell Technologies", "Dell", "DELL"],
    "HPE":               ["Hewlett Packard Enterprise", "HPE"],
    "HP Inc":            ["HP Inc", "HPQ"],
}

# ─────────────────────────────────────────────
# TICKER MAP  (company name → Yahoo Finance ticker)
# TW stocks use .TW suffix; US-listed use ticker directly
# ─────────────────────────────────────────────
TICKER_MAP = {
    "TSMC":              "TSM",
    "UMC":               "UMC",
    "MediaTek":          "2454.TW",
    "ASPEED Tech":       "5274.TW",
    "ASE Technology":    "ASX",
    "Chroma ATE":        "2360.TW",
    "Unimicron":         "3037.TW",
    "Nan Ya PCB":        "8046.TW",
    "Kinsus":            "3189.TW",
    "Gold Circuit":      "2368.TW",
    "Elite Material":    "2383.TW",
    "Tripod Tech":       "3044.TW",
    "Taiwan Union":      "6274.TW",
    "Hon Hai (Foxconn)": "2317.TW",
    "Quanta Computer":   "2382.TW",
    "Inventec":          "2356.TW",
    "Wistron":           "3231.TW",
    "Wiwynn":            "6669.TW",
    "Pegatron":          "4938.TW",
    "Compal":            "2324.TW",
    "Celestica":         "CLS",
    "Flex Ltd":          "FLEX",
    "Jabil":             "JBL",
    "ASUSTeK":           "2357.TW",
    "Acer":              "2353.TW",
    "Delta Electronics": "2308.TW",
    "Lite-On":           "2301.TW",
    "Hon Precision":     "2354.TW",
    "Lotes":             "3533.TW",
    "BizLink":           "3665.TW",
    "Jentech":           "3653.TW",
    "Accton":            "2345.TW",
    "Auras Technology":  "3324.TW",
    "Asia Vital":        "3017.TW",
    "NVIDIA":            "NVDA",
    "Intel":             "INTC",
    "Broadcom":          "AVGO",
    "AMD":               "AMD",
    "Marvell":           "MRVL",
    "Qualcomm":          "QCOM",
    "Astera Labs":       "ALAB",
    "Credo Technology":  "CRDO",
    "Micron":            "MU",
    "Lumentum":          "LITE",
    "Coherent":          "COHR",
    "Fabrinet":          "FN",
    "Apple":             "AAPL",
    "Microsoft":         "MSFT",
    "Amazon (AWS)":      "AMZN",
    "Alphabet (Google)": "GOOGL",
    "Meta":              "META",
    "Super Micro":       "SMCI",
    "Dell Technologies": "DELL",
    "HPE":               "HPE",
    "HP Inc":            "HPQ",
}

# ─────────────────────────────────────────────
# RSS FEEDS  (url, language)
# ─────────────────────────────────────────────
RSS_FEEDS = [
    # ── English ──────────────────────────────────────────────
    ("https://feeds.reuters.com/reuters/technologyNews",  "en"),   # Reuters Tech
    ("https://feeds.reuters.com/reuters/businessNews",    "en"),   # Reuters Business
    ("https://feeds.reuters.com/reuters/companyNews",     "en"),   # Reuters Company
    ("https://www.wsj.com/xml/rss/3_7085.xml",           "en"),   # WSJ Tech
    ("https://www.wsj.com/xml/rss/3_7014.xml",           "en"),   # WSJ Markets
    # ── Traditional Chinese ───────────────────────────────────
    ("https://money.udn.com/rssfeed/news/1001/5588",     "zh"),   # 經濟日報 科技
    ("https://money.udn.com/rssfeed/news/1001/5612",     "zh"),   # 經濟日報 產業
    ("https://www.cnyes.com/rss/cat/tw_stock_news",      "zh"),   # 鉅亨網 台股
]
# Bloomberg is fetched separately via NewsAPI (see fetch_bloomberg)
# Futubull is fetched separately via scraper (see fetch_futubull)


# ─────────────────────────────────────────────
# NEWS FETCHING
# ─────────────────────────────────────────────
def parse_pub_date(entry):
    for field in ("published", "updated"):
        raw = entry.get(f"{field}_parsed") or entry.get(field)
        if raw is None:
            continue
        if hasattr(raw, "tm_year"):
            return datetime(*raw[:6], tzinfo=timezone.utc)
        if isinstance(raw, str):
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss(hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []
    for url, lang in RSS_FEEDS:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "NewsScreener/1.0"})
            for entry in feed.entries:
                pub = parse_pub_date(entry)
                if pub and pub < cutoff:
                    continue
                title = entry.get("title", "").strip()
                if title:
                    articles.append({
                        "title":     title,
                        "summary":   entry.get("summary", "")[:400],
                        "link":      entry.get("link", ""),
                        "source":    feed.feed.get("title", url),
                        "published": pub.strftime("%Y-%m-%d %H:%M UTC") if pub else "unknown",
                        "lang":      lang,
                    })
        except Exception as e:
            print(f"  [RSS warn] {url}: {e}", file=sys.stderr)
    return articles


def fetch_newsapi(hours, api_key):
    """Two-pass NewsAPI fetch: Bloomberg/WSJ by source + broad semiconductor keyword query."""
    if not api_key:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    base = {
        "from": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sortBy": "publishedAt", "pageSize": 100,
        "apiKey": api_key, "language": "en",
    }
    queries = [
        {"sources": "bloomberg,the-wall-street-journal"},
        {"q": (
            "TSMC OR NVIDIA OR Intel OR Broadcom OR AMD OR Micron OR Qualcomm OR Marvell "
            "OR Foxconn OR MediaTek OR \"AI chip\" OR HBM OR CoWoS OR semiconductor "
            "OR Astera OR Credo OR Wiwynn OR \"Super Micro\" OR \"supply chain\""
        )},
    ]
    results, seen = [], set()
    for extra in queries:
        try:
            resp = requests.get("https://newsapi.org/v2/everything", timeout=15,
                                params={**base, **extra})
            resp.raise_for_status()
            for a in resp.json().get("articles", []):
                title = (a.get("title") or "").strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                results.append({
                    "title":     title,
                    "summary":   (a.get("description") or "")[:400],
                    "link":      a.get("url", ""),
                    "source":    a.get("source", {}).get("name", "NewsAPI"),
                    "published": a.get("publishedAt", "unknown"),
                    "lang":      "en",
                })
        except Exception as e:
            print(f"  [NewsAPI warn] {e}", file=sys.stderr)
    return results


def fetch_futubull(hours):
    """Scrape Futubull public news page (no login required)."""
    import re
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    # Futubull serves news via an internal JSON API called by their frontend
    # Try the public news list endpoint (no auth required for public market news)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://news.futunn.com/",
    }
    urls_to_try = [
        # Futubull internal news API endpoints (public, no auth)
        "https://news.futunn.com/news-site/api/news-list?type=1&size=50&lang=zh-TW",
        "https://news.futunn.com/news-site/api/news-list?type=1&size=50&lang=en",
    ]
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            items = data.get("data", {}).get("list") or data.get("list") or []
            lang  = "zh" if "zh-TW" in url else "en"
            for item in items:
                title   = (item.get("title") or item.get("newsTitle") or "").strip()
                summary = (item.get("summary") or item.get("content") or "")[:400]
                link    = item.get("url") or item.get("link") or ""
                pub_ts  = item.get("publishTime") or item.get("time") or 0
                if pub_ts:
                    try:
                        pub = datetime.fromtimestamp(int(str(pub_ts)[:10]), tz=timezone.utc)
                        if pub < cutoff:
                            continue
                        pub_str = pub.strftime("%Y-%m-%d %H:%M UTC")
                    except Exception:
                        pub_str = "unknown"
                else:
                    pub_str = "unknown"
                if title:
                    articles.append({
                        "title":     title,
                        "summary":   summary,
                        "link":      link,
                        "source":    "Futubull",
                        "published": pub_str,
                        "lang":      lang,
                    })
        except Exception as e:
            print(f"  [Futubull warn] {url}: {e}", file=sys.stderr)

    return articles


def match_stocks(articles):
    results = {}
    for article in articles:
        text = (article["title"] + " " + article["summary"]).lower()
        for company, keywords in WATCHLIST.items():
            for kw in keywords:
                if kw.lower() in text:
                    results.setdefault(company, [])
                    if article not in results[company]:
                        results[company].append(article)
                    break
    return results


# ─────────────────────────────────────────────
# STOCK PRICE FETCHING
# ─────────────────────────────────────────────
def fetch_prices(companies):
    """Return {company: {ticker, price, change_pct, currency}} for companies with a ticker."""
    try:
        import yfinance as yf
    except ImportError:
        print("  [price warn] yfinance not installed, skipping prices", file=sys.stderr)
        return {}

    prices = {}
    for company in companies:
        ticker_sym = TICKER_MAP.get(company)
        if not ticker_sym:
            continue
        try:
            hist = yf.Ticker(ticker_sym).history(period="5d")
            if len(hist) >= 2:
                prev  = hist["Close"].iloc[-2]
                last  = hist["Close"].iloc[-1]
                chg   = (last - prev) / prev * 100
                prices[company] = {
                    "ticker":     ticker_sym,
                    "price":      last,
                    "change_pct": chg,
                    "currency":   "TWD" if ticker_sym.endswith(".TW") else "USD",
                }
        except Exception as e:
            print(f"  [price warn] {ticker_sym}: {e}", file=sys.stderr)
    return prices


# ─────────────────────────────────────────────
# AI SCORING
# ─────────────────────────────────────────────
def score_with_claude(matched, client):
    all_articles, seen, unique = [], set(), []
    for arts in matched.values():
        all_articles.extend(arts)
    for a in all_articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    if not unique:
        return matched

    implications = {}
    for i in range(0, len(unique), 20):
        batch = unique[i:i + 20]
        items = "\n".join(
            f"{j+1}. [lang={a.get('lang','en')}] [{a['source']}] {a['title']}"
            for j, a in enumerate(batch)
        )
        prompt = (
            "You are an equity research assistant specializing in semiconductors and hardware.\n\n"
            "For each headline, write ONE concise sentence (≤20 words) on the potential implication "
            "for stock price or fundamentals (earnings, demand, margins, market share, supply chain).\n\n"
            "Language rules:\n"
            "- [lang=zh]: write implication in Traditional Chinese only.\n"
            "- [lang=en]: write in English, add Chinese translation in parentheses.\n"
            "  Example: \"Strong data center demand drives upside. （資料中心需求強勁，業績有望超預期。）\"\n"
            "- If no fundamental impact: for zh reply \"對基本面影響不大。\"; "
            "for en reply \"No significant implication. （對基本面影響不大。）\"\n\n"
            "Headlines:\n" + items + "\n\n"
            'Reply ONLY in JSON: {"1": "text", "2": "text", ...}'
        )
        try:
            response = client.messages.create(
                model="claude-opus-4-6", max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            parsed = json.loads(raw)
            for j, article in enumerate(batch):
                implications[article["title"]] = parsed.get(str(j + 1), "")
        except Exception as e:
            print(f"  [Claude warn] {e}", file=sys.stderr)
        time.sleep(0.5)

    for arts in matched.values():
        for article in arts:
            article["implication"] = implications.get(article["title"], "")
    return matched


# ─────────────────────────────────────────────
# PDF GENERATION
# ─────────────────────────────────────────────
def _load_font(pdf):
    """Try to load a CJK-capable font. Returns the font name to use."""
    candidates = [
        "C:/Windows/Fonts/msjh.ttc",       # Microsoft JhengHei (Traditional Chinese, Windows TW)
        "C:/Windows/Fonts/mingliu.ttc",     # MingLiU fallback
        "C:/Windows/Fonts/msyh.ttc",        # Microsoft YaHei (Simplified, last resort)
        "/System/Library/Fonts/PingFang.ttc",  # macOS
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdf.add_font("CJK", fname=path)
                return "CJK"
            except Exception:
                continue
    return "Helvetica"   # ASCII-only fallback


def generate_pdf(matched, prices, hours, output_path):
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    font = _load_font(pdf)
    LM = pdf.l_margin          # left margin (fixed reference)
    W  = pdf.w - LM - pdf.r_margin   # usable page width

    def reset():
        """Always reset cursor to left margin before writing a line."""
        pdf.set_x(LM)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Page title ────────────────────────────────────────────
    reset()
    pdf.set_font(font, size=18)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(W, 10, f"半導體硬體早報  {now_str}", new_x="LMARGIN", new_y="NEXT", align="C")

    reset()
    pdf.set_font(font, size=9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(W, 6,
             f"涵蓋過去 {hours} 小時  |  追蹤名單 {len(WATCHLIST)} 檔  |  共 {len(matched)} 家公司有新聞",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # ── One section per company ───────────────────────────────
    for company in sorted(matched.keys()):
        articles = matched[company]
        price    = prices.get(company)

        chg = price["change_pct"] if price else None
        if chg is None:
            r, g, b = 210, 210, 210
        elif chg >= 0:
            r, g, b = 198, 239, 206
        else:
            r, g, b = 255, 199, 206

        # --- Company header: single full-width cell, price appended right ---
        if price:
            sign    = "▲" if chg >= 0 else "▼"
            cur_sym = "NT$" if price["currency"] == "TWD" else "$"
            price_str = f"  {price['ticker']}  {cur_sym}{price['price']:.2f}  {sign}{abs(chg):.2f}%"
        else:
            price_str = ""

        reset()
        pdf.set_fill_color(r, g, b)
        pdf.set_font(font, size=12)
        pdf.set_text_color(20, 20, 20)

        W_name  = W * 0.58
        W_price = W - W_name
        pdf.cell(W_name,  9, f"  {company}",  fill=True, new_x="RIGHT",  new_y="TOP")
        pdf.cell(W_price, 9, price_str,       fill=True, new_x="LMARGIN", new_y="NEXT", align="R")

        # --- News items ---
        for idx, article in enumerate(articles, 1):
            if idx > 1:
                reset()
                pdf.set_draw_color(210, 210, 210)
                pdf.line(LM + 3, pdf.get_y(), LM + W - 3, pdf.get_y())
                pdf.ln(1)

            # Title
            reset()
            pdf.set_font(font, size=10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(W, 6, f"  {idx}. {article['title']}",
                           new_x="LMARGIN", new_y="NEXT")

            # News content / summary
            if article.get("summary"):
                reset()
                pdf.set_font(font, size=8)
                pdf.set_text_color(80, 80, 80)
                snippet = article["summary"].replace("\n", " ").strip()
                if len(snippet) > 350:
                    snippet = snippet[:350] + "…"
                pdf.multi_cell(W, 5, f"    {snippet}",
                               new_x="LMARGIN", new_y="NEXT")

            # Source · time · link
            reset()
            pdf.set_font(font, size=7)
            pdf.set_text_color(100, 100, 200)
            link = article.get("link", "")
            src_line = f"    {article['source']}  ·  {article['published']}  ·  {link}"
            pdf.multi_cell(W, 4, src_line, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        pdf.ln(4)

    pdf.output(output_path)
    return output_path


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours",  type=int, default=24)
    parser.add_argument("--out",    type=str, default=None)
    parser.add_argument("--no-pdf", action="store_true", help="Output Markdown instead of PDF")
    args = parser.parse_args()

    print(f"[1/6] 抓取 RSS：Reuters / WSJ / 經濟日報 / 鉅亨網（過去 {args.hours} 小時）…", file=sys.stderr)
    rss = fetch_rss(args.hours)
    print(f"      {len(rss)} 則", file=sys.stderr)

    print("[2/6] Bloomberg + NewsAPI broad query…", file=sys.stderr)
    newsapi = fetch_newsapi(args.hours, os.getenv("NEWSAPI_KEY", ""))
    print(f"      {len(newsapi)} 則", file=sys.stderr)

    print("[3/6] 抓取 Futubull…", file=sys.stderr)
    futu = fetch_futubull(args.hours)
    print(f"      {len(futu)} 則", file=sys.stderr)

    print("[4/6] 比對追蹤名單…", file=sys.stderr)
    matched = match_stocks(rss + newsapi + futu)
    print(f"      共 {len(matched)} 家公司命中", file=sys.stderr)

    print("[5/6] 抓取股價…", file=sys.stderr)
    prices = fetch_prices(list(matched.keys()))
    print(f"      取得 {len(prices)} 檔股價", file=sys.stderr)

    # Determine output path
    if args.out:
        out_path = args.out
    else:
        os.makedirs("briefs", exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        ext = "md" if args.no_pdf else "pdf"
        out_path = f"briefs/brief_{date_str}.{ext}"

    if args.no_pdf:
        # Markdown output (fallback)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"# 半導體硬體早報  —  {now_str}",
                 f"*涵蓋：過去 {args.hours} 小時  |  追蹤名單：{len(WATCHLIST)} 檔*", ""]
        if not matched:
            lines.append("**本時段內未發現相關新聞。**")
        else:
            for company, articles in sorted(matched.items()):
                p = prices.get(company)
                price_str = (f"  `{p['ticker']}  {'NT$' if p['currency']=='TWD' else '$'}"
                             f"{p['price']:.2f}  "
                             f"{'▲' if p['change_pct']>=0 else '▼'}{abs(p['change_pct']):.2f}%`"
                             if p else "")
                lines.append(f"## {company}{price_str}  （{len(articles)} 則）")
                for a in articles:
                    lines.append(f"- **[{a['source']}]** [{a['title']}]({a['link']})")
                    lines.append(f"  *{a['published']}*")
                    if a.get("summary"):
                        lines.append(f"  {a['summary'].replace(chr(10), ' ')[:300]}…")
                    lines.append("")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    else:
        generate_pdf(matched, prices, args.hours, out_path)

    print(f"\n報告已存至：{out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
