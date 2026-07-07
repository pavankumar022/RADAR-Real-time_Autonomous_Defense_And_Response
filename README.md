```
██████╗  █████╗ ██████╗  █████╗ ██████╗
██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗
██████╔╝███████║██║  ██║███████║██████╔╝
██╔══██╗██╔══██║██║  ██║██╔══██║██╔══██╗
██║  ██║██║  ██║██████╔╝██║  ██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
```

# RADAR — Real-time Autonomous Defense And Response
### *Enterprise-Grade Real-Time Cyber Threat Intelligence, Live Packet Capture & Autonomous Incident Response Platform*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Three.js](https://img.shields.io/badge/Three.js-3D_Globe-000000?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.0+-38BDF8?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK_v14-RED?style=for-the-badge)](https://attack.mitre.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

---

RADAR is an autonomous SOC platform that detects, visualizes, and responds to network cyber threats in real time. **No Docker required** — runs entirely on your local machine.

## 🚀 Quick Start (No Docker)

### Requirements: Python 3.10+, Node.js 18+, Git

```bash
# 1. Clone
git clone https://github.com/pavankumar022/RADAR-Real-time_Autonomous_Defense_And_Response.git
cd RADAR-Real-time_Autonomous_Defense_And_Response/radar

# 2. First-time setup (installs everything, builds frontend)
setup.bat          # Windows
bash setup.sh      # Linux / macOS

# 3. Start RADAR
start.bat          # Windows
bash start.sh      # Linux / macOS

# 4. Open browser
# http://localhost:54321
```

> **Optional:** Add your free Gemini API key to `radar/.env` to enable AI Playbooks & Incident Reports.  
> Get one at: https://aistudio.google.com/apikey

---

## 🎯 Simulate Attacks

In a second terminal (from the `radar/` folder):

```bash
# Nmap port scan simulation
python attack_tools/run_nmap_scan.py --target 192.168.1.100

# SSH brute-force simulation
python attack_tools/run_ssh_brute.py --target 192.168.1.100
```

Alerts appear instantly on the dashboard with live 3D globe animations.

---

## ✨ Features

- 🌍 **3D Attack Globe** — Live Bezier arc animations for every detected threat
- 🔴 **Live Network Capture** — Monitors real SSH, RDP, SMB, HTTP inbound connections
- 🤖 **AI Incident Playbooks** — MITRE ATT&CK-aligned auto-generated response plans
- 📋 **AI Incident Reports** — Full SOC analyst reports with IoCs and escalation notes
- 🗺️ **MITRE ATT&CK Matrix** — Live technique heatmaps from real traffic
- ⚡ **Replay Mode** — Stress-test at 500+ Events Per Second
- 📡 **Attack Simulation Tools** — Built-in Nmap & SSH brute-force simulators (pure Python)
- 🔄 **NDJSON Log Ingestion** — POST events from any external tool

---

📖 **Full documentation:** [radar/README.md](radar/README.md)
