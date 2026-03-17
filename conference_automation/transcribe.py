"""
transcribe.py
用 OpenAI Whisper API 把音檔轉成逐字稿。
自動偵測檔案大小，超過 24MB 則用 ffmpeg 切割成小塊分批轉錄。
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import openai

import config

logger = logging.getLogger(__name__)

MAX_BYTES    = 24 * 1024 * 1024  # 24MB（Whisper 上限 25MB，留 1MB 緩衝）
CHUNK_MINUTES = 10               # 每塊切 10 分鐘

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def _get_duration(audio_path: Path) -> float:
    """用 ffprobe 取得音檔總秒數。"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(audio_path)],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())


def _split_with_ffmpeg(audio_path: Path, tmp_dir: str) -> list[Path]:
    """用 ffmpeg 把音檔切成 CHUNK_MINUTES 分鐘一塊，存成 mp3。"""
    duration = _get_duration(audio_path)
    chunk_sec = CHUNK_MINUTES * 60
    chunks: list[Path] = []

    start = 0.0
    idx = 0
    while start < duration:
        out = Path(tmp_dir) / f"chunk_{idx:03d}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(audio_path),
             "-ss", str(start), "-t", str(chunk_sec),
             "-ar", "16000", "-ac", "1", "-b:a", "64k",
             str(out)],
            capture_output=True, check=True
        )
        chunks.append(out)
        start += chunk_sec
        idx += 1

    return chunks


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
    檔案超過 24MB 自動用 ffmpeg 切塊分批處理。
    """
    client = _get_client()
    file_size = audio_path.stat().st_size
    logger.info(f"[Whisper] 開始轉錄: {audio_path.name} ({file_size / 1024 / 1024:.1f} MB)")

    # 檔案夠小，直接送
    if file_size <= MAX_BYTES:
        result = _transcribe_file(client, audio_path)
        logger.info(f"[Whisper] 轉錄完成，共 {len(result)} 字元")
        return result.strip()

    # 檔案太大，用 ffmpeg 切塊
    logger.info(f"[Whisper] 檔案超過 24MB，用 ffmpeg 切割成 {CHUNK_MINUTES} 分鐘一塊...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 若路徑含非 ASCII 字元（中文檔名），先複製到 temp 目錄避免 Windows encoding 問題
        safe_path = audio_path
        if not all(ord(c) < 128 for c in str(audio_path)):
            safe_path = Path(tmp_dir) / ("input" + audio_path.suffix)
            shutil.copy2(audio_path, safe_path)
            logger.info(f"[Whisper] 偵測到非 ASCII 路徑，已複製到暫存: {safe_path.name}")
        chunks = _split_with_ffmpeg(safe_path, tmp_dir)
        total = len(chunks)
        parts: list[str] = []
        for i, chunk in enumerate(chunks):
            logger.info(f"[Whisper] 轉錄第 {i+1}/{total} 塊...")
            parts.append(_transcribe_file(client, chunk).strip())

    full = " ".join(parts)
    logger.info(f"[Whisper] 全部轉錄完成，共 {len(full)} 字元")
    return full
