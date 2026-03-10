# Raspberry Pi Robot Backend (`pi_backend`)

This folder contains a deploy-friendly FastAPI backend designed to run on a Raspberry Pi and control a Wi-Fi robot in real time over WebSocket.

## Features

- FastAPI server with:
  - `GET /` health endpoint
  - `WS /ws` robot control endpoint
- Safe mock motor functions for:
  - `forward`, `backward`, `left`, `right`, `stop`
  - `servo_pan(value)`, `servo_tilt(value)`
- Safety behavior: when WebSocket disconnects, `stop()` is always called.
- Easy run options:
  - `python3 app.py`
  - `./run.sh`

## Install dependencies

```bash
cd pi_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run backend

```bash
cd pi_backend
python3 app.py
```

Or:

```bash
cd pi_backend
chmod +x run.sh
./run.sh
```

Server starts on:

- `http://0.0.0.0:8000`
- WebSocket: `ws://<pi-ip>:8000/ws`

## Message format from frontend

Examples expected by this backend:

```json
{"command":"forward"}
{"command":"left"}
{"command":"stop"}
{"command":"servo_pan","value":120}
{"command":"servo_tilt","value":75}
```

Backend responds with JSON including `status` and `last_action`.

## How to find your Raspberry Pi IP

On the Pi, run:

```bash
hostname -I
```

Use the first IP shown (for example: `192.168.1.44`).

You can also try mDNS hostname:

- `raspberrypi.local`

## How frontend connects

In your frontend app, set WebSocket URL to:

- `ws://raspberrypi.local:8000/ws`

or:

- `ws://<pi-ip>:8000/ws`

Both devices (Pi and browser device) must be on the same Wi-Fi.

## Replacing mock motor code with GPIO later

Edit `motor_controller.py` and replace print statements with real GPIO calls (for example via `gpiozero` or `RPi.GPIO`).

Suggested approach:

1. Keep function names the same (`forward`, `stop`, etc.)
2. Add hardware initialization once at module startup.
3. Replace body of each movement/servo function with actual pin control logic.
4. Keep return values as strings so the WebSocket response format remains consistent.
