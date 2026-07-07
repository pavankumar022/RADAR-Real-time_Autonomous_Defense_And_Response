#!/usr/bin/env bash
set -e
echo "[RADAR] Building React frontend..."
cd frontend
npm run build
cd ..
rm -rf backend/dist
cp -r frontend/dist backend/dist
echo "[RADAR] Frontend built into backend/dist successfully."
