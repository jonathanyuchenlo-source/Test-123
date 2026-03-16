#!/usr/bin/env python3
"""
Daily News Screener for Semi/Hardware Analyst
Fetches news from the past 24 hours and filters by watchlist companies.

Usage:
    python news_screener.py                  # past 24 hours, output to terminal
    python news_screener.py --hours 48       # past 48 hours
    python news_screener.py --out report.md  # save to file
    python news_screener.py --no-ai          # skip Claude scoring (faster)
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# WATCHLIST  (display name → search keywords)
# ─────────────────────────────────────────────
WATCHLIST = {
    # Taiwan – Foundry / Fab
    "TSMC":             ["TSMC", "Taiwan Semiconductor", "台積電", "TSM"],
    "UMC":              ["UMC", "United Microelectronics", "聯電"],
    # Taiwan – Fabless / Design
    "MediaTek":         ["MediaTek", "聯發科", "MTK"],
    "ASPEED Tech":      ["ASPEED", "信驊"],
    # Taiwan – OSAT
    "ASE Technology":   ["ASE Technology", "ASE Group", "日月光", "ASX"],
    # Taiwan – Test Equipment
    "Chroma ATE":       ["Chroma", "致茂"],
    # Taiwan – PCB / Substrate
    "Unimicron":        ["Unimicron", "欣興"],
    "Nan Ya PCB":       ["Nan Ya PCB", "Nan Ya Printed", "南亞電路板"],
    "Kinsus":           ["Kinsus", "景碩"],
    "Gold Circuit":     ["Gold Circuit", "GCE", "健鼎"],
    "Elite Material":   ["Elite Material", "EMC", "利佳"],
    "Tripod Tech":      ["Tripod Technology", "健鼎科技"],
    "Taiwan Union":     ["Taiwan Union", "台燿"],
    # Taiwan – EMS / ODM
    "Hon Hai (Foxconn)": ["Hon Hai", "Foxconn", "鴻海", "富士康"],
    "Quanta Computer":  ["Quanta Computer", "廣達"],
    "Inventec":         ["Inventec", "英業達"],
    "Wistron":          ["Wistron", "緯創"],
    "Wiwynn":           ["Wiwynn", "緯穎"],
    "Pegatron":         ["Pegatron", "和碩"],
    "Compal":           ["Compal", "仁寶"],
    "Celestica":        ["Celestica", "CLS"],
    "Flex Ltd":         ["Flex Ltd", "Flextronics"],
    "Jabil":            ["Jabil"],
    # Taiwan – Brand PC
    "ASUSTeK":          ["ASUS", "ASUSTeK", "華碩"],
    "Acer":             ["Acer", "宏碁"],
    # Taiwan – Power / Passive
    "Delta Electronics": ["Delta Electronics", "台達電"],
    "Lite-On":          ["Lite-On", "光寶"],
    # Taiwan – Connector / Cable
    "Hon Precision":    ["Hon Precision", "鴻準"],
    "Lotes":            ["Lotes", "正崴"],
    "BizLink":          ["BizLink", "彼洋"],
    "Jentech":          ["Jentech", "健策"],
    # Taiwan – Networking
    "Accton":           ["Accton", "智邦"],
    # Taiwan – Thermal
    "Auras Technology": ["Auras", "雙鴻"],
    "Asia Vital":       ["Asia Vital", "AVC", "建準"],
    # US – Semiconductor
    "NVIDIA":           ["NVIDIA", "NVDA", "Nvidia"],
    "Intel":            ["Intel", "INTC"],
    "Broadcom":         ["Broadcom", "AVGO"],
    "AMD":              ["AMD", "Advanced Micro Devices"],
    "Marvell":          ["Marvell Technology", "Marvell", "MRVL"],
    "Qualcomm":         ["Qualcomm", "QCOM"],
    "Astera Labs":      ["Astera Labs", "ALAB"],
    "Credo Technology": ["Credo Technology", "CRDO"],
    "Micron":           ["Micron Technology", "Micron", "MU"],
    "Lumentum":         ["Lumentum", "LITE"],
    "Coherent":         ["Coherent Corp", "COHR"],
    "Fabrinet":         ["Fabrinet", "FN"],
    # US – End Market / Hyperscaler
    "Apple":            ["Apple", "AAPL"],
    "Microsoft":        ["Microsoft", "MSFT"],
    "Amazon (AWS)":     ["Amazon", "AWS", "AMZN"],
    "Alphabet (Google)": ["Alphabet", "Google", "GOOGL"],
    "Meta":             ["Meta Platforms", "Meta", "Facebook", "META"],
    # US – Server / Infrastructure
    "Super Micro":      ["Super Micro", "Supermicro", "SMCI"],
    "Dell Technologies": ["Dell Technologies", "Dell", "DELL"],
    "HPE":              ["Hewlett Packard Enterprise", "HPE"],
    "HP Inc":           ["HP Inc", "HPQ"],
}

# ─────────────────────────────────────────────
# RSS FEEDS
# ─────────────────────────────────────────────
RSS_FEEDS = [
    # English – Tech / Business
    "https://feeds.reuters.com/reuters/technologyNews",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.reuters.com/reuters/companyNews",
    "https://www.wsj.com/xml/rss/3_7085.xml",           # WSJ Tech
    "https://www.wsj.com/xml/rss/3_7014.xml",           # WSJ Markets
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA,TSM,INTC,AVGO,AMD,MU,MRVL,QCOM",
    # Traditional Chinese – TW
    "https://www.chinatimes.com/rss/industry.xml",      # 工商時報 – 產業
    "https://www.chinatimes.com/rss/tech.xml",          # 工商時報 – 科技
    "https://www.cnyes.com/rss/cat/tw_stock_news",      # 鉅亨網 – 台股
    "https://money.udn.com/rssfeed/news/1001/5588",     # 經濟日報 – 科技
    "https://money.udn.com/rssfeed/news/1001/5612",     # 經濟日報 – 產業
]


def parse_pub_date(entry) -> datetime | None:
    """Return UTC-aware datetime from a feedparser entry, or None."""
    for field in ("published", "updated"):
        raw = entry.get(f"{field}_parsed") or entry.get(field)
        if raw is None:
            continue
        if hasattr(raw, "tm_year"):          # time.struct_time from feedparser
            return datetime(*raw[:6], tzinfo=timezone.utc)
        if isinstance(raw, str):
            try:
                dt = parsedate_to_datetime(raw)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss(hours: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "NewsScreener/1.0"})
            for entry in feed.entries:
                pub = parse_pub_date(entry)
                if pub and pub < cutoff:
                    continue          # too old
                title = entry.get("title", "").strip()
                link  = entry.get("link", "").strip()
                summary = entry.get("summary", "")[:300]
                if title:
                    articles.append({
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "source": feed.feed.get("title", url),
                        "published": pub.strftime("%Y-%m-%d %H:%M UTC") if pub else "unknown",
                    })
        except Exception as e:
            print(f"  [RSS warn] {url}: {e}", file=sys.stderr)
    return articles


def fetch_newsapi(hours: int, api_key: str) -> list[dict]:
    if not api_key:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    from_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build a focused query from high-profile tickers
    query = (
        "TSMC OR NVIDIA OR Intel OR Broadcom OR AMD OR Micron OR Qualcomm OR Marvell "
        "OR Foxconn OR MediaTek OR ASML OR semiconductor OR AI chip OR HBM OR CoWoS"
    )
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_str,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 100,
        "apiKey": api_key,
    }
    articles = []
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        for a in resp.json().get("articles", []):
            articles.append({
                "title":     a.get("title", "").strip(),
                "summary":   (a.get("description") or "")[:300],
                "link":      a.get("url", ""),
                "source":    a.get("source", {}).get("name", "NewsAPI"),
                "published": a.get("publishedAt", "unknown"),
            })
    except Exception as e:
        print(f"  [NewsAPI warn] {e}", file=sys.stderr)
    return articles


def match_stocks(articles: list[dict]) -> dict[str, list[dict]]:
    """Return {company_name: [matched articles]} for articles mentioning watchlist companies."""
    results: dict[str, list[dict]] = {}
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


def score_with_claude(matched: dict[str, list[dict]], client: Anthropic) -> dict[str, list[dict]]:
    """Add an 'implication' field to each article using Claude."""
    all_articles = []
    for articles in matched.values():
        all_articles.extend(articles)
    # Deduplicate
    seen = set()
    unique = []
    for a in all_articles:
        key = a["title"]
        if key not in seen:
            seen.add(key)
            unique.append(a)

    if not unique:
        return matched

    # Batch into groups of 20 to keep prompts manageable
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    implications: dict[str, str] = {}

    for batch in chunks(unique, 20):
        items = "\n".join(
            f"{i+1}. [{a['source']}] {a['title']}"
            for i, a in enumerate(batch)
        )
        prompt = (
            "You are an equity research assistant specializing in semiconductors and hardware.\n"
            "For each news headline below, write ONE concise sentence (max 20 words) describing "
            "the potential implication for the company's stock price or fundamentals "
            "(e.g. earnings, demand, margins, market share, supply chain). "
            "If a headline is unlikely to move fundamentals, reply 'No significant implication'.\n\n"
            "Headlines:\n" + items + "\n\n"
            "Reply in this exact JSON format:\n"
            '{"1": "implication text", "2": "implication text", ...}'
        )
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            # Extract JSON even if wrapped in markdown
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            parsed = __import__("json").loads(raw)
            for i, article in enumerate(batch):
                implications[article["title"]] = parsed.get(str(i + 1), "")
        except Exception as e:
            print(f"  [Claude warn] {e}", file=sys.stderr)
        time.sleep(0.5)   # be polite to the API

    # Write implications back
    for company, articles in matched.items():
        for article in articles:
            article["implication"] = implications.get(article["title"], "")
    return matched


def build_report(matched: dict[str, list[dict]], hours: int, use_ai: bool) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Daily News Brief  —  {now_str}",
        f"*Coverage: past {hours} hours  |  Watchlist: {len(WATCHLIST)} companies*",
        "",
    ]
    if not matched:
        lines.append("**No relevant news found in this window.**")
        return "\n".join(lines)

    lines.append(f"**{len(matched)} companies with news hits:**  "
                 + ", ".join(matched.keys()))
    lines.append("")

    for company, articles in sorted(matched.items()):
        lines.append(f"## {company}  ({len(articles)} articles)")
        for a in articles:
            lines.append(f"- **[{a['source']}]** [{a['title']}]({a['link']})")
            lines.append(f"  *{a['published']}*")
            if use_ai and a.get("implication"):
                lines.append(f"  > {a['implication']}")
            if a.get("summary"):
                snippet = a["summary"].replace("\n", " ")[:200]
                lines.append(f"  {snippet}…")
            lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Daily news screener for semi/hardware watchlist")
    parser.add_argument("--hours", type=int, default=24, help="Look-back window in hours (default: 24)")
    parser.add_argument("--out",   type=str, default=None, help="Save report to file (e.g. report.md)")
    parser.add_argument("--no-ai", action="store_true", help="Skip Claude AI relevance scoring")
    args = parser.parse_args()

    newsapi_key    = os.getenv("NEWSAPI_KEY", "")
    anthropic_key  = os.getenv("ANTHROPIC_API_KEY", "")
    use_ai = not args.no_ai and bool(anthropic_key)

    print(f"[1/4] Fetching RSS feeds (past {args.hours}h)…", file=sys.stderr)
    rss_articles = fetch_rss(args.hours)
    print(f"      {len(rss_articles)} articles from RSS", file=sys.stderr)

    print("[2/4] Fetching NewsAPI…", file=sys.stderr)
    api_articles = fetch_newsapi(args.hours, newsapi_key)
    print(f"      {len(api_articles)} articles from NewsAPI", file=sys.stderr)

    all_articles = rss_articles + api_articles

    print("[3/4] Matching against watchlist…", file=sys.stderr)
    matched = match_stocks(all_articles)
    print(f"      {len(matched)} companies with hits", file=sys.stderr)

    if use_ai and matched:
        print("[4/4] Scoring with Claude…", file=sys.stderr)
        client = Anthropic(api_key=anthropic_key)
        matched = score_with_claude(matched, client)
    else:
        print("[4/4] Skipping AI scoring", file=sys.stderr)

    report = build_report(matched, args.hours, use_ai)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nReport saved to {args.out}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
