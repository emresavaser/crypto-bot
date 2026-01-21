@echo off
echo ========================================
echo   ECLIPSE SCALPER API BRIDGE
echo ========================================
echo.

cd /d "%~dp0"

REM Python virtual environment kontrolu
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM API Bridge'i baslat
cd api_bridge
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

pause
