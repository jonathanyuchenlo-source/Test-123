"""
memo.py
用 Claude API 把逐字稿轉成結構化投資筆記。
"""

from __future__ import annotations

import logging
from datetime import date

import anthropic

import config

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None

SYSTEM_PROMPT = """你現在是一位避險基金的股票研究助理 (Equity Research Associate)。

目的與目標 (Purpose and Goals):
* 將語音轉文字程式生成的科技行業會議逐字稿，整理成一份專業、結構化、內容完整且易於複習的詳細筆記。
* 利用專業知識，識別並修正逐字稿中可能因錯誤識別而產生的文字錯誤或關鍵詞錯誤。
* 筆記內容必須忠實於逐字稿的陳述，不得加入個人的想法。

行為與規則 (Behaviors and Rules):
1) 筆記生成步驟 (Note Generation Steps):
    a) 你將收到四項資訊：1) 會議日期、2) 會議主題、3) Speaker、4) 會議逐字稿。
    b) 將筆記標題命名為：'會議日期 會議主題'。
    c) 以股票研究助理的專業視角，對逐字稿內容進行審核、修正和分類整理。特別注意科技行業的專業術語和關鍵數據。
    d) 重點關注並完整記錄以下關鍵細節：
        i.  數字、百分比、變化率等量化數據。
        ii. 爭論雙方各自提出的所有論點還有詳細。
        iii. 支撐論點的證據 (Evidence) 和數據。
        iv. 任何重要的聲明或結論。

2) 內容結構與格式 (Content Structure and Format):
    a) 筆記內容必須以分類列點的方式呈現，依據逐字稿中不同的主題或發言者來設置分類標題。
    b) 確保每個字體大小一致 (純文字 不使用粗體 or 符號)。
    c) 筆記必須涵蓋逐字稿中的所有重要細節。

整體語氣 (Overall Tone):
* 保持專業、精確和客觀的語氣。
* 展現出對科技行業和財務分析的深刻理解。"""

DRAFT_PROMPT = """以下是會議資訊，請整理成結構化筆記：

會議日期：{meeting_date}
會議主題：{topic}
Speaker：{speaker}

<transcript>
{transcript}
</transcript>

After drafting the notes, immediately perform a second pass: re-check every number, percentage, date, company name, product name, and technical term against the original transcript. Fix any errors or hallucinations. Make sure you have included every key point. If any part is unclear from the transcript, mark it as [unclear] rather than guessing. Output ONLY the final corrected version. Do not show the draft."""


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


def generate_memo(
    transcript: str,
    audio_filename: str = "",
    meeting_date: str = "",
    topic: str = "",
    speaker: str = "",
) -> str:
    """
    生成投資筆記（含內建二次校對）。

    Args:
        transcript: Whisper 輸出的逐字稿
        audio_filename: 原始音檔名稱（topic/meeting_date 未提供時作為 fallback）
        meeting_date: 會議日期（e.g. 2026/3/17）
        topic: 會議主題
        speaker: 發言者

    Returns:
        最終筆記字串（純文字）
    """
    resolved_date = meeting_date or date.today().strftime("%Y/%m/%d")
    resolved_topic = topic or audio_filename or "Conference Recording"
    resolved_speaker = speaker or "N/A"

    logger.info("[Claude] 生成筆記（含內建二次校對）...")
    return _call(
        DRAFT_PROMPT.format(
            meeting_date=resolved_date,
            topic=resolved_topic,
            speaker=resolved_speaker,
            transcript=transcript,
        )
    )
