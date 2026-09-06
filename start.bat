@echo off
title Vancouver Rental Finder
echo.
echo  ============================================
echo    Vancouver Rental Finder - Starting up
echo  ============================================
echo.

if "%ANTHROPIC_API_KEY%"=="" (
  echo  [!] ANTHROPIC_API_KEY is not set.
  echo      Set it with:  set ANTHROPIC_API_KEY=sk-ant-...
  echo      Then re-run this script.
  echo.
  pause
  exit /b 1
)

if not exist "venv" (
  echo  [1/3] Creating virtual environment...
  python -m venv venv
)

echo  [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo  [3/3] Starting server...
echo.
echo  Open your browser at:  http://localhost:8000
echo  Press Ctrl+C to stop.
echo.

cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
