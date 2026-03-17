"""
main.py
會議錄音全自動化流水線：
  音檔 → Whisper 轉錄 → Claude 生成 memo → 本地資料夾（暫時跳過 OneNote）

使用方式：
  python main.py              # 監聽模式（持續監控資料夾）
  python main.py <音檔路徑>    # 單次處理指定音檔
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from docx import Document
from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

import config
from memo import generate_memo
from transcribe import transcribe

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Processed Files Log ───────────────────────────────────────────────────────

def _load_processed() -> set[str]:
    if config.PROCESSED_LOG.exists():
        return set(config.PROCESSED_LOG.read_text().splitlines())
    return set()


def _mark_processed(path: Path) -> None:
    with open(config.PROCESSED_LOG, "a") as f:
        f.write(str(path.resolve()) + "\n")


# ── Core Pipeline ─────────────────────────────────────────────────────────────

def process_audio(audio_path: Path) -> None:
    """
    完整流水線：音檔 → 逐字稿 → memo → OneNote
    """
    processed = _load_processed()
    key = str(audio_path.resolve())

    if key in processed:
        logger.info(f"[跳過] 已處理過: {audio_path.name}")
        return

    logger.info(f"\n{'='*60}")
    logger.info(f"🎙  開始處理: {audio_path.name}")
    logger.info(f"{'='*60}")

    # Step 1: 語音轉文字
    transcript = transcribe(audio_path)
    logger.info(f"✅ Step 1/3 轉錄完成（{len(transcript)} 字元）")

    # Step 2: 生成 memo（Claude，兩步驟）
    memo = generate_memo(transcript, audio_filename=audio_path.stem)
    logger.info(f"✅ Step 2/3 Memo 生成完成（{len(memo)} 字元）")

    # Step 3: 存到本地 Memos 資料夾（Word 文件）
    output_dir = Path(config.OUTPUT_FOLDER)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (audio_path.stem + ".docx")
    doc = Document()
    for line in memo.splitlines():
        doc.add_paragraph(line)
    doc.save(str(output_path))
    logger.info(f"✅ Step 3/3 Memo 已儲存 → {output_path}")

    _mark_processed(audio_path)
    logger.info(f"🎉 完成！{audio_path.name}\n")


# ── Watchdog Handler ──────────────────────────────────────────────────────────

class AudioHandler(FileSystemEventHandler):
    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in config.AUDIO_EXTENSIONS:
            return

        # 等 2 秒確保檔案寫入完成
        time.sleep(2)
        try:
            process_audio(path)
        except Exception as e:
            logger.error(f"處理失敗 {path.name}: {e}", exc_info=True)


# ── Entry Point ───────────────────────────────────────────────────────────────

def watch_folder() -> None:
    folder = config.WATCH_FOLDER
    if not folder.exists():
        logger.error(f"監控資料夾不存在: {folder}")
        logger.error("請在 .env 中設定正確的 WATCH_FOLDER 路徑")
        sys.exit(1)

    logger.info(f"👁  開始監控資料夾: {folder}")
    logger.info("（把音檔存入此資料夾，自動觸發全流程）\n")

    observer = Observer()
    observer.schedule(AudioHandler(), str(folder), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("已停止監控。")
    observer.join()


def main() -> None:
    if len(sys.argv) > 1:
        # 單次處理模式
        audio_path = Path(sys.argv[1])
        if not audio_path.exists():
            logger.error(f"找不到音檔: {audio_path}")
            sys.exit(1)
        process_audio(audio_path)
    else:
        # 監聽模式
        watch_folder()


if __name__ == "__main__":
    main()
