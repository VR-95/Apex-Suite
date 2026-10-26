@echo off
REM ─────────────────────────────────────────────────────────────
REM  Apex Suite — one-command start (Windows)
REM  Starts both the FastAPI backend and the React frontend.
REM ─────────────────────────────────────────────────────────────

echo Apex Suite -- starting...
echo.

IF NOT EXIST "backend\.env" (
  echo backend\.env not found.
  echo Copy backend\.env.example to backend\.env and add your Groq keys first.
  echo copy backend\.env.example backend\.env
  exit /b 1
)

echo Starting backend on http://localhost:8000 ...
cd backend
IF NOT EXIST "venv" (
  python -m venv venv
  call venv\Scripts\pip install -r requirements.txt --quiet
)
start "Apex Suite Backend" cmd /k "venv\Scripts\uvicorn main:app --port 8000"
cd ..

timeout /t 3 /nobreak >nul

echo Starting frontend on http://localhost:5173 ...
echo.
echo Open http://localhost:5173 in your browser
echo (Close both terminal windows to stop the servers)
echo.

npm run dev
