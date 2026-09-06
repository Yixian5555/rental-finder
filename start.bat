@echo off
setlocal enabledelayedexpansion
title Vancouver Rental Finder
cls

echo.
echo  ====================================================
echo    Vancouver Rental Finder
echo  ====================================================
echo.

:: ─── Load saved API key from .env ───────────────────────
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="ANTHROPIC_API_KEY" set ANTHROPIC_API_KEY=%%b
  )
)

:: ─── Skip wizard if key is already set ──────────────────
if not "!ANTHROPIC_API_KEY!"=="" (
  echo  API key found. Starting the app...
  echo.
  goto :install_deps
)

:: ─── First-time setup wizard ────────────────────────────
cls
echo.
echo  ====================================================
echo    Welcome! Let's get you set up.
echo  ====================================================
echo.
echo  This app uses Claude AI to understand what you're
echo  looking for in a rental. It needs an API key to
echo  work — here's how to get one for free:
echo.
echo  STEP 1.  Open this link in your browser:
echo.
echo           https://console.anthropic.com
echo.
echo  STEP 2.  Create a free account (or sign in).
echo.
echo  STEP 3.  In the left menu, click  "API Keys".
echo.
echo  STEP 4.  Click "Create Key", give it any name,
echo           then click "Copy" to copy the key.
echo.
echo  STEP 5.  Come back here and paste it below.
echo.
echo  ─────────────────────────────────────────────────────
echo   The key looks like:  sk-ant-api03-XXXXXXXX...
echo  ─────────────────────────────────────────────────────
echo.
echo   Press  S  to skip for now (the chat won't work)
echo   Press  Q  to quit
echo.
set /p USER_INPUT="  Paste your API key and press Enter: "
echo.

:: Handle non-key inputs
if /i "!USER_INPUT!"=="Q" (
  echo  Goodbye!
  timeout /t 2 /nobreak > nul
  exit /b 0
)
if /i "!USER_INPUT!"=="S" (
  echo  Skipping API key setup.
  echo  You can add it later: create a file called  .env
  echo  in this folder and add the line:
  echo    ANTHROPIC_API_KEY=your-key-here
  echo.
  goto :install_deps
)
if "!USER_INPUT!"=="" (
  echo  Nothing entered — skipping for now.
  echo.
  goto :install_deps
)

:: Basic check — key should start with sk-ant
echo !USER_INPUT! | findstr /i "sk-ant" > nul
if errorlevel 1 (
  echo  ─────────────────────────────────────────────────────
  echo   [!] That doesn't look like a valid API key.
  echo       Keys start with  sk-ant-...
  echo.
  echo       Please close this window, re-open start.bat,
  echo       and try pasting the key again.
  echo  ─────────────────────────────────────────────────────
  echo.
  pause
  exit /b 1
)

:: Save key to .env for next time
echo ANTHROPIC_API_KEY=!USER_INPUT!> .env
set ANTHROPIC_API_KEY=!USER_INPUT!
echo  Your key has been saved. You won't need to enter
echo  it again next time you open the app.
echo.

:: ─── Install Python dependencies ────────────────────────
:install_deps
if not exist "venv" (
  echo  ─────────────────────────────────────────────────────
  echo   Setting things up for the first time...
  echo   (This takes about 30 seconds — only happens once)
  echo  ─────────────────────────────────────────────────────
  echo.
  python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q 2>nul

:: ─── Start the app ───────────────────────────────────────
cls
echo.
echo  ====================================================
echo    Vancouver Rental Finder is ready!
echo  ====================================================
echo.
echo  Opening your browser in 3 seconds...
echo.
echo  If the browser doesn't open, go to:
echo    http://localhost:8000
echo.
echo  To stop the app, press  Ctrl + C  in this window.
echo  ====================================================
echo.

:: Open browser automatically after a short delay
start /b cmd /c "timeout /t 3 /nobreak > nul && start http://localhost:8000"

cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
