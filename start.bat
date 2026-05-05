@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo  ============================================
echo    AI Studio - Animated Video Generation
echo  ============================================
echo.

if not exist ".venv\Scripts\activate.bat" (
  echo  [ERROR] Python venv not found at .venv\
  echo          Run: python -m venv .venv
  echo               .venv\Scripts\pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo  [ERROR] Frontend dependencies missing.
  echo          Run: cd frontend ^&^& npm install
  echo.
  pause
  exit /b 1
)

echo  [1/2] Launching backend   ^> http://localhost:8000
start "AI Studio :: Backend"  /D "%ROOT%"          cmd /k "call .venv\Scripts\activate.bat && uvicorn backend.app:app --reload"

echo  [2/2] Launching frontend  ^> http://localhost:5173
start "AI Studio :: Frontend" /D "%ROOT%frontend" cmd /k "npm run dev"

echo.
echo  Two terminal windows opened.
echo  Open http://localhost:5173 once both show "ready".
echo  Close those windows (or Ctrl+C in each) to stop the servers.
echo.
endlocal
