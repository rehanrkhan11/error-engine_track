@echo off
REM ============================================================
REM  Multi-Agent Error Engine — Windows Setup Script
REM  Run this ONCE from inside the backend\ folder.
REM  Requires Python 3.11 or 3.12 installed from python.org
REM ============================================================

echo.
echo [1/5] Checking Python version...
py -3.11 --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo      Found Python 3.11 - OK
    SET PYVER=3.11
) ELSE (
    py -3.12 --version >nul 2>&1
    IF %ERRORLEVEL% EQU 0 (
        echo      Found Python 3.12 - OK
        SET PYVER=3.12
    ) ELSE (
        echo.
        echo      ERROR: Python 3.11 or 3.12 not found!
        echo      Please download from: https://www.python.org/downloads/
        echo      Install 3.11.x or 3.12.x — NOT 3.14
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [2/5] Creating virtual environment with Python %PYVER%...
IF EXIST .venv (
    echo      Removing old .venv first...
    rmdir /s /q .venv
)
py -%PYVER% -m venv .venv
echo      Done.

echo.
echo [3/5] Activating virtual environment...
call .venv\Scripts\activate.bat
echo      Done.

echo.
echo [4/5] Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo      ERROR: pip install failed. See output above.
    pause
    exit /b 1
)
echo      Done.

echo.
echo [5/5] Creating .env file from template...
IF NOT EXIST .env (
    copy .env.example .env >nul
    echo      Created .env — OPEN IT NOW and paste your API keys!
) ELSE (
    echo      .env already exists — skipping copy.
)

echo.
echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo.
echo   Next steps:
echo   1. Open .env and paste your real API keys
echo      - Google: https://aistudio.google.com/app/apikey
echo      - Groq:   https://console.groq.com/keys
echo.
echo   2. Start the server (run this each time):
echo      .venv\Scripts\activate
echo      uvicorn app.main:app --reload --port 8000
echo.
echo   3. Test it:
echo      curl http://localhost:8000/health
echo      OR open: http://localhost:8000/docs
echo.
pause
