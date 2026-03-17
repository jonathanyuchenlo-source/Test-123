"""
transcribe.py
用 OpenAI Whisper API 把音檔轉成逐字稿。
自動偵測檔案大小，超過 24MB 則切割成小塊分批轉錄。
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import openai
from pydub import AudioSegment

import config

logger = logging.getLogger(__name__)

MAX_BYTES = 24 * 1024 * 1024   # 24MB（Whisper 上限 25MB，留 1MB 緩衝）
CHUNK_MINUTES = 10              # 每塊切 10 分鐘

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def _transcribe_file(client: openai.OpenAI, path: Path) -> str:
    """送單一檔案到 Whisper API。"""
    with open(path, "rb") as f:
        kwargs: dict = {
            "model": config.WHISPER_MODEL,
            "file": f,
            "response_format": "text",
        }
        if config.WHISPER_LANGUAGE != "auto":
            kwargs["language"] = config.WHISPER_LANGUAGE
        return client.audio.transcriptions.create(**kwargs)


def transcribe(audio_path: Path) -> str:
    """
    把音檔送到 Whisper API，回傳逐字稿文字。
    檔案超過 24MB 自動切塊分批處理。

    Args:
        audio_path: 音檔路徑（.m4a / .mp3 等）

    Returns:
        逐字稿字串
    """
    client = _get_client()
    file_size = audio_path.stat().st_size
    logger.info(f"[Whisper] 開始轉錄: {audio_path.name} ({file_size / 1024 / 1024:.1f} MB)")

    # 檔案夠小，直接送
    if file_size <= MAX_BYTES:
        result = _transcribe_file(client, audio_path)
        logger.info(f"[Whisper] 轉錄完成，共 {len(result)} 字元")
        return result.strip()

    # 檔案太大，切塊處理
    logger.info(f"[Whisper] 檔案超過 24MB，自動切割成 {CHUNK_MINUTES} 分鐘一塊...")
    audio = AudioSegment.from_file(audio_path)
    chunk_ms = CHUNK_MINUTES * 60 * 1000
    total_chunks = (len(audio) + chunk_ms - 1) // chunk_ms

    parts: list[str] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, start_ms in enumerate(range(0, len(audio), chunk_ms)):
            chunk = audio[start_ms: start_ms + chunk_ms]
            chunk_path = Path(tmp_dir) / f"chunk_{i:03d}.mp3"
            chunk.export(chunk_path, format="mp3", bitrate="64k")

            logger.info(f"[Whisper] 轉錄第 {i+1}/{total_chunks} 塊...")
            text = _transcribe_file(client, chunk_path)
            parts.append(text.strip())

    full_transcript = " ".join(parts)
    logger.info(f"[Whisper] 全部轉錄完成，共 {len(full_transcript)} 字元")
    return full_transcript
