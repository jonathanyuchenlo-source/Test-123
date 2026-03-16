#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_daily.sh  —  Smart daily wrapper for news_screener.py
#
# Logic:
#   Monday    → --hours 72  (covers Fri 8am → Mon 8am)
#   Tue–Fri   → --hours 24
#
# Setup (run once):
#   chmod +x run_daily.sh
#   crontab -e
#   Add:  0 8 * * 1-5 /path/to/this/folder/run_daily.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/briefs"
mkdir -p "$OUTPUT_DIR"

DATE_STR=$(date +"%Y-%m-%d")
DAY_OF_WEEK=$(date +"%u")   # 1=Mon … 7=Sun

if [ "$DAY_OF_WEEK" -eq 1 ]; then
    HOURS=72
    LABEL="週末補掃 (72h)"
else
    HOURS=24
    LABEL="每日早報 (24h)"
fi

OUT_FILE="$OUTPUT_DIR/brief_${DATE_STR}.md"

echo "[$DATE_STR 08:00] 開始抓取：$LABEL"

cd "$SCRIPT_DIR"
python news_screener.py --hours "$HOURS" --out "$OUT_FILE"

echo "報告已存至：$OUT_FILE"

# ── 可選：用 Python 寄信到自己 ──────────────────────────────────────────────
# 如果要自動寄 Email，取消以下注解並設定好 SMTP 設定
# python send_email.py --subject "[$DATE_STR] 半導體早報" --body "$OUT_FILE"
