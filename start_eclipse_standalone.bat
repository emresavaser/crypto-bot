@echo off
echo ========================================
echo   ECLIPSE SCALPER - STANDALONE
echo   (API Bridge olmadan dogrudan calistirma)
echo ========================================
echo.

cd /d "%~dp0"

REM Python virtual environment kontrolu
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Eclipse Scalper'i dogrudan baslat
cd eclipse_scalper
python main.py --dry-run

pause
