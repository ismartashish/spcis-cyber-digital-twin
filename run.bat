@echo off
echo =======================================================
echo   SPCIS - Self-Playing Cyber Immune System
echo   Launching Cyber Defense Command Center...
echo =======================================================
echo.

REM Activate virtual environment if available
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found on PATH. Please install Python 3.10+
    pause
    exit /b 1
)

echo Starting SPCIS API Server and Web UI on http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
python server.py --host 127.0.0.1 --port 8000
pause
