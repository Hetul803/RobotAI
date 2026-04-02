# RobotAI

RobotAI is a two-part rover control project built around a Raspberry Pi backend and a browser dashboard.

## Architecture

- `web_app/` runs in the browser on a laptop or phone
- `pi_backend/` runs on the Raspberry Pi
- the frontend talks to the Pi over Wi-Fi using REST, WebSocket, and a camera stream

## Project layout

- `pi_backend/` — FastAPI backend, mock-safe hardware controllers, autonomy logic, and camera stream
- `web_app/` — React dashboard for control, telemetry, and camera viewing

## Quick start

### Raspberry Pi backend

```bash
cd pi_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Edit only `pi_backend/config.py` for wiring, limits, ports, and runtime options.

### Frontend dashboard

```bash
cd web_app
npm install
npm run dev
```

## Simple Pi + Mac workflow

1. Copy `pi_backend/` to the Raspberry Pi.
2. Edit `pi_backend/config.py` (wiring + runtime settings).
3. Run `python3 app.py` on the Pi.
4. Run the frontend on your Mac.
5. Use the backend URL printed by `app.py` and connect.

## Modes

- Manual drive for quick hardware checks
- Obstacle avoidance for local autonomous driving with LiDAR safety
- Waypoint-by-command for scripted command sequences such as `forward 10` and `right 90`

## Deployment notes

- Copy the full `pi_backend/` folder to the Raspberry Pi.
- Adjust wiring and safety values in `pi_backend/config.py` only.
- Enable `robot.service` if you want the backend to start at boot.
