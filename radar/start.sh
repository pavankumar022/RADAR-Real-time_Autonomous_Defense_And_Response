#!/usr/bin/env bash
set -e

echo ""
echo " ██████╗  █████╗ ██████╗  █████╗ ██████╗ "
echo " ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗"
echo " ██████╔╝███████║██║  ██║███████║██████╔╝ "
echo " ██╔══██╗██╔══██║██║  ██║██╔══██║██╔══██╗ "
echo " ██║  ██║██║  ██║██████╔╝██║  ██║██║  ██║ "
echo " ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"
echo ""
echo " Real-time Autonomous Defense And Response"
echo " =========================================="
echo " Starting RADAR..."
echo ""

# ─── Check .venv exists ───────────────────────────────────────────────────────
if [ ! -f ".venv/bin/python" ] && [ ! -f ".venv/bin/python3" ]; then
    echo " ERROR: Virtual environment not found."
    echo " Please run 'bash setup.sh' first!"
    echo ""
    exit 1
fi

# ─── Check backend/dist exists ───────────────────────────────────────────────
if [ ! -f "backend/dist/index.html" ]; then
    echo " [INFO] Frontend not built yet. Building now..."
    cd frontend
    npm run build
    cd ..
    rm -rf backend/dist
    cp -r frontend/dist backend/dist
    echo " [OK] Frontend built."
fi

# ─── Check .env exists ───────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo " [INFO] Created .env from .env.example (demo mode - no AI keys)."
fi

echo " [OK] All checks passed."
echo ""
echo " ============================================================"
echo "  RADAR is starting at: http://localhost:54321"
echo " ============================================================"
echo ""
echo "  API Docs:   http://localhost:54321/api/docs"
echo "  Dashboard:  http://localhost:54321"
echo ""
echo "  To stop RADAR, press Ctrl+C in this window."
echo ""

# ─── Start backend (serves frontend + API from single port) ──────────────────
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 54321 --reload
