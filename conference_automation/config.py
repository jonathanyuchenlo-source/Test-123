"""
Configuration for Conference Recording Automation
讀取環境變數，集中管理所有設定
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY    = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# ── Microsoft / OneNote ───────────────────────────────────────────────────────
MS_CLIENT_ID     = os.getenv("MS_CLIENT_ID", "")       # Azure app client_id
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")   # Azure app client_secret
MS_TENANT_ID     = os.getenv("MS_TENANT_ID", "common") # Azure tenant_id (or "common")

# OneNote 目的地
ONENOTE_NOTEBOOK = os.getenv("ONENOTE_NOTEBOOK", "Investment Memos")  # Notebook 名稱
ONENOTE_SECTION  = os.getenv("ONENOTE_SECTION",  "Conference Notes")  # Section 名稱

# ── Watch Folder ──────────────────────────────────────────────────────────────
# 放你的 iCloud Drive / Dropbox 同步資料夾路徑
WATCH_FOLDER = Path(os.getenv("WATCH_FOLDER", str(Path.home() / "iCloud Drive/Voice Memos")))

# 支援的音檔格式
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".aac", ".ogg", ".webm"}

# ── Claude ────────────────────────────────────────────────────────────────────
CLAUDE_MODEL     = "claude-opus-4-6"
CLAUDE_MAX_TOKENS = 8000

# ── Whisper ───────────────────────────────────────────────────────────────────
WHISPER_MODEL    = "whisper-1"
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")  # zh = 中文, en = 英文, auto = 自動偵測

# ── Output ───────────────────────────────────────────────────────────────────
# Memo 存放資料夾（之後接 OneNote 時這步會變成上傳）
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", str(Path.home() / "Documents" / "ConferenceMemos"))

# ── Misc ──────────────────────────────────────────────────────────────────────
PROCESSED_LOG = Path(os.getenv("PROCESSED_LOG", "./processed_files.txt"))
