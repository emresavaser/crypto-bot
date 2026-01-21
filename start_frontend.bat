@echo off
echo ========================================
echo   CRYPTO BOT FRONTEND
echo ========================================
echo.

cd /d "%~dp0"

REM Frontend'i baslat
cd crypto-bot-ui
npm run dev

pause
