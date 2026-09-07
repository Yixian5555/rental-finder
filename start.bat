@echo off
setlocal enabledelayedexpansion
title Vancouver Rental Finder
cls

echo.
echo  ====================================================
echo    Vancouver Rental Finder
echo  ====================================================
echo.

:: Load saved keys from .env
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if "%%a"=="ANTHROPIC_API_KEY" set ANTHROPIC_API_KEY=%%b
    if "%%a"=="OPENAI_API_KEY"    set OPENAI_API_KEY=%%b
  )
)

:: Always ask which AI to use
echo  Which AI do you want to use today?
echo.
if not "!ANTHROPIC_API_KEY!"=="" (
  echo    1  Claude  (Anthropic)  [key saved]
) else (
  echo    1  Claude  (Anthropic)
)
if not "!OPENAI_API_KEY!"=="" (
  echo    2  ChatGPT (OpenAI)     [key saved]
) else (
  echo    2  ChatGPT (OpenAI)
)
echo    Q  Quit
echo.
set /p AI_CHOICE="  Enter 1 or 2: "
echo.

if /i "!AI_CHOICE!"=="Q" ( echo  Goodbye! & timeout /t 2 /nobreak > nul & exit /b 0 )

if "!AI_CHOICE!"=="1" (
  set CHOSEN_PROVIDER=claude
  set CHOSEN_LABEL=Claude
  set CHOSEN_KEY=!ANTHROPIC_API_KEY!
)
if "!AI_CHOICE!"=="2" (
  set CHOSEN_PROVIDER=openai
  set CHOSEN_LABEL=ChatGPT
  set CHOSEN_KEY=!OPENAI_API_KEY!
)
if "!CHOSEN_PROVIDER!"=="" (
  echo  Invalid choice - defaulting to Claude.
  set CHOSEN_PROVIDER=claude
  set CHOSEN_LABEL=Claude
  set CHOSEN_KEY=!ANTHROPIC_API_KEY!
)

:: Save the chosen provider as the default
if exist ".env" (
  findstr /v /i "^DEFAULT_PROVIDER=" .env > .env.tmp
  echo DEFAULT_PROVIDER=!CHOSEN_PROVIDER!>> .env.tmp
  move /y .env.tmp .env > nul
) else (
  echo DEFAULT_PROVIDER=!CHOSEN_PROVIDER!> .env
)
set DEFAULT_PROVIDER=!CHOSEN_PROVIDER!

:: Run key wizard if the chosen key is not saved
if not "!CHOSEN_KEY!"=="" goto :install_deps

:: ─── Key wizard ──────────────────────────────────────
cls
echo.
echo  ====================================================
echo    !CHOSEN_LABEL! API Key Setup
echo  ====================================================
echo.

if "!CHOSEN_PROVIDER!"=="claude" (
  echo  1. Go to: https://console.anthropic.com
  echo  2. Sign in and click "API Keys" in the left menu
  echo  3. Click "Create Key", then copy it
  echo.
  echo  The key looks like:  sk-ant-api03-XXXXXXXX...
  echo.
  set KEY_PREFIX=sk-ant
)
if "!CHOSEN_PROVIDER!"=="openai" (
  echo  1. Go to: https://platform.openai.com/api-keys
  echo  2. Sign in and click "Create new secret key"
  echo  3. Copy the key
  echo.
  echo  The key looks like:  sk-proj-XXXXXXXX... or sk-XXXXXXXX...
  echo.
  set KEY_PREFIX=sk-
)

echo  Press S to skip (the chat won't work without a key)
echo  Press Q to quit
echo.
set /p USER_KEY="  Paste your !CHOSEN_LABEL! API key: "
echo.

if /i "!USER_KEY!"=="Q" ( echo  Goodbye! & timeout /t 2 /nobreak > nul & exit /b 0 )
if /i "!USER_KEY!"=="S" ( echo  Skipping key setup. & goto :install_deps )
if "!USER_KEY!"==""       ( echo  Nothing entered - skipping. & goto :install_deps )

echo !USER_KEY! | findstr /i "sk-" > nul
if errorlevel 1 (
  echo  [!] That doesn't look like a valid API key.
  echo      Skipping for now - re-run start.bat to try again.
  goto :install_deps
)

if "!CHOSEN_PROVIDER!"=="claude" (
  set ANTHROPIC_API_KEY=!USER_KEY!
  if exist ".env" (
    findstr /v /i "^ANTHROPIC_API_KEY=" .env > .env.tmp
    echo ANTHROPIC_API_KEY=!USER_KEY!>> .env.tmp
    move /y .env.tmp .env > nul
  ) else (
    echo ANTHROPIC_API_KEY=!USER_KEY!> .env
  )
)
if "!CHOSEN_PROVIDER!"=="openai" (
  set OPENAI_API_KEY=!USER_KEY!
  if exist ".env" (
    findstr /v /i "^OPENAI_API_KEY=" .env > .env.tmp
    echo OPENAI_API_KEY=!USER_KEY!>> .env.tmp
    move /y .env.tmp .env > nul
  ) else (
    echo OPENAI_API_KEY=!USER_KEY!> .env
  )
)
echo  Key saved. You won't need to enter it again.
echo.

:: ─── Install Python dependencies ─────────────────────
:install_deps

python --version > nul 2>&1
if errorlevel 1 (
  echo  ---------------------------------------------------
  echo   [ERROR] Python not found.
  echo   Install Python 3.10+ from https://python.org
  echo   and tick "Add Python to PATH".
  echo  ---------------------------------------------------
  pause
  exit /b 1
)

if not exist "venv" (
  echo  ---------------------------------------------------
  echo   Setting things up for the first time...
  echo   (This takes about 30 seconds - only happens once)
  echo  ---------------------------------------------------
  echo.
  python -m venv venv
  if errorlevel 1 (
    echo  [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
  )
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q
if errorlevel 1 (
  echo  [WARNING] Some packages may not have installed correctly.
  echo.
)

:: ─── Start the app ────────────────────────────────────
cls
echo.
echo  ====================================================
echo    Vancouver Rental Finder is ready!
echo    Using: !CHOSEN_LABEL!
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

start /b cmd /c "timeout /t 3 /nobreak > nul && start http://localhost:8000"

cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
