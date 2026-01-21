@echo off
echo ========================================
echo   BAGIMLILIK KURULUMU
echo ========================================
echo.

cd /d "%~dp0"

REM Python virtual environment olustur
if not exist "venv" (
    echo Python virtual environment olusturuluyor...
    python -m venv venv
)

REM Aktive et
call venv\Scripts\activate.bat

REM API Bridge bagimliliklari
echo.
echo API Bridge bagimliliklari kuruluyor...
pip install -r api_bridge\requirements.txt

REM Eclipse Scalper bagimliliklari
echo.
echo Eclipse Scalper bagimliliklari kuruluyor...
pip install -r eclipse_scalper\requirements.txt

echo.
echo ========================================
echo   KURULUM TAMAMLANDI!
echo ========================================
echo.
echo Simdi calistirmak icin:
echo   1. start_backend.bat   (API Bridge)
echo   2. start_frontend.bat  (Web Arayuzu)
echo.

pause
