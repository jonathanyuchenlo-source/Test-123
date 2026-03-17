"""
transcribe.py
用 OpenAI Whisper API 把音檔轉成逐字稿
"""

from __future__ import annotations

import logging
from pathlib import Path

import openai

import config

logger = logging.getLogger(__name__)

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def transcribe(audio_path: Path) -> str:
    """
    把音檔送到 Whisper API，回傳逐字稿文字。

    Args:
        audio_path: 音檔路徑（.m4a / .mp3 等）

    Returns:
        逐字稿字串
    """
    client = _get_client()
    logger.info(f"[Whisper] 開始轉錄: {audio_path.name}")

    with open(audio_path, "rb") as f:
        kwargs: dict = {
            "model": config.WHISPER_MODEL,
            "file": f,
            "response_format": "text",
        }
        if config.WHISPER_LANGUAGE != "auto":
            kwargs["language"] = config.WHISPER_LANGUAGE

        transcript: str = client.audio.transcriptions.create(**kwargs)

    logger.info(f"[Whisper] 轉錄完成，共 {len(transcript)} 字元")
    return transcript.strip()
