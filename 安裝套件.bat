@echo off
chcp 65001 > nul
echo ================================================
echo  新聞篩選器 — 安裝必要套件（只需執行一次）
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

echo [1/2] 正在安裝必要套件...
pip install feedparser requests anthropic python-dotenv

echo.
echo [2/2] 安裝完成！
echo.
echo 下一步：
echo   1. 用記事本開啟同資料夾內的 ".env" 檔案
echo   2. 填入你的 NEWSAPI_KEY 和 ANTHROPIC_API_KEY
echo   3. 儲存後，執行「每日執行.bat」
echo.
pause
