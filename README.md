# RobotAI: Wi-Fi Robot Control Project

This repository is a complete two-part robotics control setup:

- `pi_backend/` → runs on Raspberry Pi (FastAPI + WebSocket control server)
- `web_app/` → runs in browser (React + Vite control dashboard)

## Architecture

`Frontend Web App` ⇄ `Wi-Fi Network` ⇄ `Raspberry Pi Backend`

1. Web app sends real-time JSON commands over WebSocket.
2. Pi backend parses commands and calls motor/servo functions.
3. Backend returns status + last action JSON responses.
4. On disconnect, backend executes `stop()` for safety.

## Folder overview

- `pi_backend/`
  - `app.py` FastAPI app + WebSocket endpoint `/ws`
  - `motor_controller.py` mock movement + servo functions
  - `config.py` host/port configuration
  - `requirements.txt`, `run.sh`, and backend README

- `web_app/`
  - React + Vite app with responsive futuristic UI
  - WebSocket connection controls and command sender
  - telemetry cards + command log panel
  - frontend README for run and network usage

## Quick start

### Backend (Raspberry Pi)

```bash
cd pi_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

### Frontend (Laptop/dev machine)

```bash
cd web_app
npm install
npm run dev
```

Then open browser and connect to:

- `ws://raspberrypi.local:8000/ws` (or Pi IP)

## Deployment-friendly notes

- No Docker
- No database
- No auth complexity
- Minimal dependencies
- Backend can be deployed by copying entire `pi_backend/` folder to Raspberry Pi
