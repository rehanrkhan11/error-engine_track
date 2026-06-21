@echo off
REM ============================================================
REM  Run this every time you want to start the dev server.
REM  Must be run from inside the backend\ folder.
REM ============================================================
call .venv\Scripts\activate.bat
echo Virtual environment activated.
echo Starting server at http://localhost:8000
echo API docs at    http://localhost:8000/docs
echo Press CTRL+C to stop.
echo.
uvicorn app.main:app --reload --port 8000
