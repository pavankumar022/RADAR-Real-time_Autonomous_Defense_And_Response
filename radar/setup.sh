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
echo " FIRST-TIME SETUP  |  Linux / macOS"
echo ""

# ─── Check Python ─────────────────────────────────────────────────────────────
echo "[1/6] Checking Python version..."
if ! command -v python3 &>/dev/null; then
    echo ""
    echo " ERROR: python3 is not installed."
    echo " Ubuntu/Debian:  sudo apt install python3 python3-venv python3-pip"
    echo " macOS:          brew install python"
    echo ""
    exit 1
fi
PY_VER=$(python3 --version 2>&1)
echo " [OK] $PY_VER found."

# ─── Check Node.js ────────────────────────────────────────────────────────────
echo "[2/6] Checking Node.js version..."
if ! command -v node &>/dev/null; then
    echo ""
    echo " ERROR: Node.js is not installed."
    echo " Install from: https://nodejs.org/  (v18+ recommended)"
    echo " Or via nvm:   nvm install --lts"
    echo ""
    exit 1
fi
NODE_VER=$(node --version 2>&1)
echo " [OK] Node.js $NODE_VER found."

# ─── Create Python virtual environment ───────────────────────────────────────
echo "[3/6] Creating Python virtual environment (.venv)..."
if [ -d ".venv" ]; then
    echo " [SKIP] .venv already exists."
else
    python3 -m venv .venv
    echo " [OK] Virtual environment created."
fi

# ─── Install Python dependencies ─────────────────────────────────────────────
echo "[4/6] Installing Python dependencies..."
.venv/bin/pip install -r backend/requirements.txt -q
echo " [OK] Python dependencies installed."

# ─── Install Node.js dependencies ────────────────────────────────────────────
echo "[5/6] Installing frontend dependencies (npm install)..."
cd frontend
npm install --silent
cd ..
echo " [OK] Frontend dependencies installed."

# ─── Build frontend ───────────────────────────────────────────────────────────
echo "[6/6] Building React frontend into backend/dist ..."
cd frontend
npm run build
cd ..

rm -rf backend/dist
cp -r frontend/dist backend/dist
echo " [OK] Frontend built and copied to backend/dist"

# ─── Setup .env ───────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo " [INFO] Created .env from .env.example"
    echo " [INFO] The app works in demo mode without API keys."
    echo " [INFO] To enable AI features, open .env and add your GEMINI_API_KEY."
fi

echo ""
echo " ============================================================"
echo "  Setup complete!"
echo " ============================================================"
echo ""
echo "  To start RADAR, run:"
echo "    bash start.sh"
echo ""
echo "  Then open your browser at:"
echo "    http://localhost:54321"
echo ""
echo "  To simulate attacks (in another terminal):"
echo "    python3 attack_tools/run_nmap_scan.py --target <TARGET_IP>"
echo "    python3 attack_tools/run_ssh_brute.py --target <TARGET_IP>"
echo ""
