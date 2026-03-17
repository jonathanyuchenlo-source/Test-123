"""
onenote.py
透過 Microsoft Graph API 把 memo 存入 OneNote。
使用 MSAL Device Code Flow（適合本機腳本，第一次執行時開瀏覽器登入）。
Token 快取到 ~/.conference_auto_token_cache.bin，之後不用再登入。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import msal
import requests

import config

logger = logging.getLogger(__name__)

SCOPES = ["Notes.ReadWrite", "Notes.ReadWrite.All"]
TOKEN_CACHE_PATH = Path.home() / ".conference_auto_token_cache.bin"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


# ── Token Management ──────────────────────────────────────────────────────────

def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text())
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        TOKEN_CACHE_PATH.write_text(cache.serialize())


def _get_token() -> str:
    cache = _load_cache()
    app = msal.PublicClientApplication(
        client_id=config.MS_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{config.MS_TENANT_ID}",
        token_cache=cache,
    )

    # 嘗試用快取的帳號靜默取得 token
    accounts = app.get_accounts()
    result = app.acquire_token_silent(SCOPES, account=accounts[0]) if accounts else None

    if not result:
        # 第一次執行：device code flow（終端顯示 URL + code，開瀏覽器掃 QR 即可）
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow 初始化失敗: {flow.get('error_description')}")
        print("\n" + "=" * 60)
        print("請在瀏覽器開啟以下網址並輸入代碼：")
        print(f"  URL : {flow['verification_uri']}")
        print(f"  Code: {flow['user_code']}")
        print("=" * 60 + "\n")
        result = app.acquire_token_by_device_flow(flow)

    _save_cache(cache)

    if "access_token" not in result:
        raise RuntimeError(f"取得 token 失敗: {result.get('error_description')}")

    return result["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── OneNote Helpers ───────────────────────────────────────────────────────────

def _get_or_create_notebook(token: str, name: str) -> str:
    """取得或建立 Notebook，回傳 notebook_id。"""
    r = requests.get(f"{GRAPH_BASE}/me/onenote/notebooks", headers=_headers(token))
    r.raise_for_status()
    for nb in r.json().get("value", []):
        if nb["displayName"] == name:
            return nb["id"]

    r = requests.post(
        f"{GRAPH_BASE}/me/onenote/notebooks",
        headers=_headers(token),
        json={"displayName": name},
    )
    r.raise_for_status()
    return r.json()["id"]


def _get_or_create_section(token: str, notebook_id: str, name: str) -> str:
    """取得或建立 Section，回傳 section_id。"""
    r = requests.get(
        f"{GRAPH_BASE}/me/onenote/notebooks/{notebook_id}/sections",
        headers=_headers(token),
    )
    r.raise_for_status()
    for sec in r.json().get("value", []):
        if sec["displayName"] == name:
            return sec["id"]

    r = requests.post(
        f"{GRAPH_BASE}/me/onenote/notebooks/{notebook_id}/sections",
        headers=_headers(token),
        json={"displayName": name},
    )
    r.raise_for_status()
    return r.json()["id"]


def _markdown_to_html(markdown: str) -> str:
    """
    把 Markdown 轉成簡單 HTML（OneNote 只吃 HTML）。
    用 markdown-it-py 處理，已列在 requirements.txt。
    """
    from markdown_it import MarkdownIt
    md = MarkdownIt()
    return md.render(markdown)


# ── Public API ────────────────────────────────────────────────────────────────

def save_to_onenote(memo_markdown: str, page_title: str) -> str:
    """
    把 memo 存入 OneNote。

    Args:
        memo_markdown: Markdown 格式的 memo 內容
        page_title: OneNote 頁面標題

    Returns:
        新建頁面的 URL
    """
    logger.info(f"[OneNote] 準備儲存: {page_title}")

    token = _get_token()
    notebook_id = _get_or_create_notebook(token, config.ONENOTE_NOTEBOOK)
    section_id  = _get_or_create_section(token, notebook_id, config.ONENOTE_SECTION)

    html_body = _markdown_to_html(memo_markdown)
    page_html = f"""<!DOCTYPE html>
<html>
  <head>
    <title>{page_title}</title>
    <meta name="created" content="{__import__('datetime').datetime.utcnow().isoformat()}Z"/>
  </head>
  <body>
    {html_body}
  </body>
</html>"""

    r = requests.post(
        f"{GRAPH_BASE}/me/onenote/sections/{section_id}/pages",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/xhtml+xml",
        },
        data=page_html.encode("utf-8"),
    )
    r.raise_for_status()

    page_url = r.json().get("links", {}).get("oneNoteWebUrl", {}).get("href", "(URL 未回傳)")
    logger.info(f"[OneNote] 儲存成功 → {page_url}")
    return page_url
