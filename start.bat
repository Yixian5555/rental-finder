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

:: Skip wizard if at least one key is already set
if not "!ANTHROPIC_API_KEY!"=="" goto :install_deps
if not "!OPENAI_API_KEY!"==""    goto :install_deps

:: ─── First-time setup wizard ─────────────────────────
cls
echo.
echo  ====================================================
echo    Welcome! Let's get you set up.
echo  ====================================================
echo.
echo  This app uses an AI to understand what you're
echo  looking for in a rental. You can use Claude (by
echo  Anthropic) or ChatGPT (by OpenAI) - or both.
echo.
echo  Which AI would you like to set up?
echo.
echo    1  Claude  (https://console.anthropic.com)
echo    2  ChatGPT (https://platform.openai.com/api-keys)
echo    3  Both
echo    S  Skip for now
echo    Q  Quit
echo.
set /p PROVIDER_CHOICE="  Enter 1, 2, 3, S or Q: "
echo.

if /i "!PROVIDER_CHOICE!"=="Q" ( echo  Goodbye! & timeout /t 2 /nobreak > nul & exit /b 0 )
if /i "!PROVIDER_CHOICE!"=="S" goto :install_deps

if "!PROVIDER_CHOICE!"=="1" goto :setup_claude
if "!PROVIDER_CHOICE!"=="3" goto :setup_claude
if "!PROVIDER_CHOICE!"=="2" goto :setup_openai

echo  Invalid choice. Skipping setup.
goto :install_deps

:: ─── Claude key wizard ───────────────────────────────
:setup_claude
echo  ---------------------------------------------------
echo   Setting up Claude
echo  ---------------------------------------------------
echo.
echo  1. Go to: https://console.anthropic.com
echo  2. Sign in and click "API Keys" in the left menu
echo  3. Click "Create Key", then copy it
echo.
echo  The key looks like:  sk-ant-api03-XXXXXXXX...
echo.
echo  Press S to skip Claude and continue
echo.
set /p CLAUDE_KEY="  Paste your Claude API key: "
echo.

if /i "!CLAUDE_KEY!"=="S" goto :after_claude

echo !CLAUDE_KEY! | findstr /i "sk-ant" > nul
if errorlevel 1 (
  echo  [!] That doesn't look like a Claude key (should start with sk-ant-...)
  echo      Skipping Claude setup.
  goto :after_claude
)

set ANTHROPIC_API_KEY=!CLAUDE_KEY!
if exist ".env" (
  findstr /v /i "^ANTHROPIC_API_KEY=" .env > .env.tmp
  echo ANTHROPIC_API_KEY=!CLAUDE_KEY!>> .env.tmp
  move /y .env.tmp .env > nul
) else (
  echo ANTHROPIC_API_KEY=!CLAUDE_KEY!> .env
)
echo  Claude key saved.
echo.

:after_claude
if not "!PROVIDER_CHOICE!"=="3" goto :install_deps

:: ─── OpenAI key wizard ───────────────────────────────
:setup_openai
echo  ---------------------------------------------------
echo   Setting up ChatGPT (OpenAI)
echo  ---------------------------------------------------
echo.
echo  1. Go to: https://platform.openai.com/api-keys
echo  2. Sign in and click "Create new secret key"
echo  3. Copy the key
echo.
echo  The key looks like:  sk-proj-XXXXXXXX... or sk-XXXXXXXX...
echo.
echo  Press S to skip ChatGPT and continue
echo.
set /p OPENAI_KEY="  Paste your OpenAI API key: "
echo.

if /i "!OPENAI_KEY!"=="S" goto :install_deps

echo !OPENAI_KEY! | findstr /i "^sk-" > nul
if errorlevel 1 (
  echo  [!] That doesn't look like an OpenAI key (should start with sk-...)
  echo      Skipping ChatGPT setup.
  goto :install_deps
)

set OPENAI_API_KEY=!OPENAI_KEY!
if exist ".env" (
  findstr /v /i "^OPENAI_API_KEY=" .env > .env.tmp
  echo OPENAI_API_KEY=!OPENAI_KEY!>> .env.tmp
  move /y .env.tmp .env > nul
) else (
  echo OPENAI_API_KEY=!OPENAI_KEY!> .env
)
echo  ChatGPT key saved.
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
