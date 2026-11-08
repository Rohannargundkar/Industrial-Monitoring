@echo off
title Industrial Monitoring System
cd /d "%~dp0"

echo ============================================================
echo        INDUSTRIAL MONITORING SYSTEM
echo ============================================================
echo.

REM Uses the virtual environment if it exists, otherwise system Python
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

start "Flask Server" %PY% app.py
timeout /t 2 /nobreak >nul
start "ESP32 Serial Bridge" %PY% esp32_serial.py
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5000

echo Dashboard : http://127.0.0.1:5000
echo Close the two console windows to stop the system.
echo.
pause
