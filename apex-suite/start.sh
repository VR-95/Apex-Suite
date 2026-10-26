#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Apex Suite — one-command start (Mac / Linux)
#  Starts both the FastAPI backend and the React frontend.
# ─────────────────────────────────────────────────────────────
set -e

echo "⚡ Apex Suite — starting..."
echo ""

# Check for backend/.env
if [ ! -f "backend/.env" ]; then
  echo "⚠️  backend/.env not found."
  echo "   Copy backend/.env.example to backend/.env and add your Groq keys first."
  echo "   cp backend/.env.example backend/.env"
  exit 1
fi

# Start backend in the background
echo "→ Starting backend on http://localhost:8000 ..."
cd backend
if [ ! -d "venv" ]; then
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt --quiet
fi
./venv/bin/uvicorn main:app --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend
echo "→ Starting frontend on http://localhost:5173 ..."
echo ""
echo "✅ Open http://localhost:5173 in your browser"
echo "   (Press Ctrl+C to stop both servers)"
echo ""

trap "kill $BACKEND_PID 2>/dev/null" EXIT
npm run dev
