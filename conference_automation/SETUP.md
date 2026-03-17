# 會議錄音自動化 — 設定指南

## 架構

```
iPhone Voice Memo
    ↓ (iCloud/Dropbox 自動同步)
本地監控資料夾（watchdog）
    ↓
OpenAI Whisper API（語音 → 文字）
    ↓
Claude API claude-opus-4-6（生成 memo + 校對）
    ↓
Microsoft Graph API
    ↓
OneNote 指定 Notebook / Section ✅
```

## 快速開始

### 1. 安裝套件

```bash
cd conference_automation
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 用任何編輯器開啟 .env 填入 API keys
```

### 3. 建立 Azure App（取得 OneNote 存取權）

1. 前往 [Azure Portal](https://portal.azure.com)
2. **App registrations** → **New registration**
3. Name 隨意，Supported account types 選 **Personal Microsoft accounts**
4. Redirect URI 選 `Public client/native` → `http://localhost`
5. 建立後複製 **Application (client) ID** → 填入 `MS_CLIENT_ID`
6. **API permissions** → Add permission → Microsoft Graph → Delegated
   → 搜尋 `Notes.ReadWrite` → 加入
7. **Certificates & secrets** → New client secret → 複製 → 填入 `MS_CLIENT_SECRET`

### 4. 設定 iPhone Voice Memo 同步

**iCloud 方式（推薦）：**
- iPhone：設定 → iCloud → iCloud Drive → 開啟
- Voice Memo App 的錄音會自動出現在 iCloud Drive
- Mac 的 iCloud Drive 路徑：
  ```
  ~/Library/Mobile Documents/com~apple~CloudDocs/
  ```

**Dropbox 方式：**
- iPhone 安裝 Dropbox App
- Voice Memo 錄完後手動分享到 Dropbox（或用 Shortcuts App 自動化）

### 5. 執行

**監聽模式（推薦）：**
```bash
python main.py
```
把音檔存入監控資料夾後，全流程自動觸發。

**單次處理：**
```bash
python main.py /path/to/meeting.m4a
```

## 使用 iOS Shortcuts 進一步自動化

在 iPhone 上建立 Shortcut：
1. 觸發條件：Voice Memo 結束錄音
2. 動作：分享最新錄音 → 儲存到 iCloud Drive / Dropbox 指定資料夾

這樣手機錄完就自動上傳，Mac 端自動偵測 → 全流程跑完，完全無需手動操作。

## 費用估算（每次會議）

| 服務 | 費用 |
|------|------|
| Whisper（60 分鐘） | ~$0.36 |
| Claude Opus 4.6（2次呼叫） | ~$0.10–0.30 |
| Microsoft Graph API | 免費 |
| **合計** | **< $0.70** |

## 檔案結構

```
conference_automation/
├── main.py          # 入口點、資料夾監控
├── transcribe.py    # Whisper API
├── memo.py          # Claude API（生成 + 校對）
├── onenote.py       # Microsoft Graph API
├── config.py        # 環境變數讀取
├── requirements.txt
├── .env.example     # 環境變數範本
└── SETUP.md         # 本文件
```
