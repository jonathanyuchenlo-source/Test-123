@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ================================================
echo  半導體硬體早報 — 安裝 + 執行
echo ================================================
echo.

:: 確認 Python 已安裝
python --version > nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python！
    echo 請先到 https://www.python.org/downloads/ 安裝 Python
    echo 安裝時記得勾選 "Add python.exe to PATH"
    pause
    exit /b 1
)

echo [1/3] 安裝必要套件（第一次約需 1 分鐘）...
pip install -q feedparser requests anthropic python-dotenv yfinance fpdf2

echo [2/3] 確認設定檔...
if not exist ".env" (
    echo [錯誤] 找不到 .env 檔案！
    echo 請確認 .env 檔案和本程式放在同一個資料夾。
    pause
    exit /b 1
)

echo [3/3] 開始執行...
echo.

if not exist "briefs" mkdir briefs

:: 判斷今天是否為週一（自動補掃週末）
for /f %%d in ('powershell -command "(Get-Date).DayOfWeek.value__"') do set DOW=%%d
if "%DOW%"=="1" (
    set HOURS=72
    echo 週一模式：補掃過去 72 小時（含週末）
) else (
    set HOURS=24
    echo 每日模式：掃描過去 24 小時
)

for /f %%d in ('powershell -command "Get-Date -Format 'yyyy-MM-dd'"') do set DATE_STR=%%d
set OUT_FILE=briefs\brief_%DATE_STR%.pdf

python news_screener.py --hours %HOURS% --out %OUT_FILE%

if errorlevel 1 (
    echo.
    echo [錯誤] 執行失敗，請確認 .env 內的 API Key 是否正確。
    pause
    exit /b 1
)

echo.
echo 完成！正在開啟 PDF 報告...
start "" "%OUT_FILE%"
pause
