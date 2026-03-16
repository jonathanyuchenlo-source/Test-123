@echo off
chcp 65001 > nul

:: 切換到這個批次檔所在的資料夾
cd /d "%~dp0"

:: 建立 briefs 資料夾（如果不存在）
if not exist "briefs" mkdir briefs

:: 取得今天日期 (YYYY-MM-DD)
for /f "tokens=1-3 delims=/" %%a in ('powershell -command "Get-Date -Format 'yyyy/MM/dd'"') do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set DATE_STR=%YEAR%-%MONTH%-%DAY%

:: 判斷今天是否為週一（自動補掃週末）
for /f %%d in ('powershell -command "(Get-Date).DayOfWeek.value__"') do set DOW=%%d
if "%DOW%"=="1" (
    set HOURS=72
    echo [%DATE_STR%] 週一模式：補掃過去 72 小時（含週末）
) else (
    set HOURS=24
    echo [%DATE_STR%] 每日模式：掃描過去 24 小時
)

set OUT_FILE=briefs\brief_%DATE_STR%.md

echo 開始抓取新聞，請稍候...
echo.

python news_screener.py --hours %HOURS% --out %OUT_FILE%

if errorlevel 1 (
    echo.
    echo [錯誤] 執行失敗，請確認 .env 檔案內的 API Key 是否正確填寫
    pause
    exit /b 1
)

echo.
echo ✓ 完成！報告已儲存至：%OUT_FILE%
echo.

:: 用預設程式開啟報告（Markdown 可用 VS Code、Typora、或記事本）
echo 是否要立即開啟報告？（按任意鍵開啟，按 X 後 Enter 略過）
set /p OPEN=
if /i not "%OPEN%"=="X" (
    start "" "%OUT_FILE%"
)
