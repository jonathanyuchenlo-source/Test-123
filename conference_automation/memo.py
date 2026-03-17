"""
memo.py
用 Claude API 把逐字稿轉成結構化投資 memo，再做一輪校對。
"""

from __future__ import annotations

import logging
from datetime import date

import anthropic

import config

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None

SYSTEM_PROMPT = """你是一位頂尖對沖基金的資深分析師助理。
你的工作是把會議錄音的逐字稿整理成清晰、專業的投資 memo。
請用繁體中文輸出。若逐字稿為英文，摘要仍請用繁體中文，
關鍵英文術語可附括號原文，例如：資本支出（CapEx）。"""

DRAFT_PROMPT = """以下是今天會議的錄音逐字稿，請整理成結構化投資 memo：

<transcript>
{transcript}
</transcript>

請依以下格式輸出（Markdown）：

## 📋 會議摘要
（2-3 句話，總覽核心主題）

## 🏢 公司/標的
（提到的公司名稱、股票代碼）

## 💡 關鍵洞察
- （重要觀點，條列式）

## 📊 關鍵數據
| 指標 | 數值 | 備註 |
|------|------|------|
| ... | ... | ... |

## ⚠️ 風險提示
- （潛在風險，條列式）

## ✅ 行動項目
- [ ] （需跟進的事項，附負責人/截止日期若有提及）

## 💬 其他備注
（其他值得記錄的細節）"""

REVIEW_PROMPT = """請再次仔細檢查以下投資 memo，確保：
1. 所有數字、日期、公司名稱正確無誤
2. 沒有遺漏重要資訊
3. 行動項目清單完整
4. 格式整齊，Markdown 語法正確
5. 沒有前後矛盾的陳述

若有錯誤或遺漏，直接修正後輸出完整 memo；若已完整無誤，直接輸出原 memo 即可。

<memo>
{draft}
</memo>"""


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _call(prompt: str) -> str:
    client = _get_client()
    with client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=config.CLAUDE_MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        return stream.get_final_message().content[-1].text


def generate_memo(transcript: str, audio_filename: str = "") -> str:
    """
    兩步驟生成投資 memo：
      1. 草稿（Draft）：根據逐字稿整理
      2. 校對（Review）：再過一遍確保無誤

    Args:
        transcript: Whisper 輸出的逐字稿
        audio_filename: 原始音檔名稱（用於 memo 標題）

    Returns:
        最終 memo 字串（Markdown）
    """
    today = date.today().strftime("%Y-%m-%d")
    title = audio_filename or "Conference Recording"

    # Step 1: 產生草稿
    logger.info("[Claude] Step 1/2 – 生成 memo 草稿...")
    draft = _call(DRAFT_PROMPT.format(transcript=transcript))

    # Step 2: 校對
    logger.info("[Claude] Step 2/2 – 校對細節...")
    final = _call(REVIEW_PROMPT.format(draft=draft))

    # 加上標頭
    header = f"# 會議記錄 – {title}\n**日期：** {today}\n\n---\n\n"
    return header + final
