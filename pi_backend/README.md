# pi_backend

FastAPI backend for a Raspberry Pi rover. It exposes the control API, telemetry stream, mock-safe hardware controllers, waypoint execution, obstacle avoidance, and a browser-friendly camera stream.

## Files

- `app.py` — FastAPI app and route wiring
- `config.py` — all wiring, limits, and tuning values
- `motor_controller.py` — DC motor control
- `steering_controller.py` — front steering servo and camera pan servo
- `lidar_controller.py` — LiDAR readings and simple directional scans
- `camera_controller.py` — MJPEG video stream
- `autonomy_controller.py` — obstacle avoidance loop
- `command_executor.py` — waypoint-by-command parsing and execution
- `state.py` — shared rover state and telemetry
- `robot.service` — optional systemd service

## Install dependencies

```bash
cd pi_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the backend

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

The API listens on `http://0.0.0.0:8000` by default.

## Edit wiring and tuning

Open `config.py` and update the motor pins, servo channels, steering limits, camera pan limits, LiDAR connection values, safety thresholds, speeds, and video settings.

Set `MOCK_MODE = True` while developing without hardware. Set it to `False` when you replace the mock controller internals with real hardware calls.

## Find the Pi IP address

```bash
hostname -I
```

Use the first IP address in the output. You can also try `raspberrypi.local` on the same network.

## Frontend connection

Open the dashboard and point it to your Pi backend, for example:

- `http://raspberrypi.local:8000`
- `http://192.168.1.44:8000`

The frontend uses:

- WebSocket telemetry at `/ws`
- camera stream at `/video`
- REST routes for mode changes, waypoint submission, and emergency stop

## Enable auto-start with systemd

Copy `robot.service` into systemd, then enable it:

```bash
sudo cp robot.service /etc/systemd/system/robot.service
sudo systemctl daemon-reload
sudo systemctl enable robot.service
sudo systemctl start robot.service
sudo systemctl status robot.service
```

If your project lives somewhere else, update `WorkingDirectory` and `ExecStart` inside `robot.service` first.

## API overview

- `GET /`
- `GET /state`
- `GET /config`
- `POST /mode`
- `POST /stop`
- `POST /waypoints`
- `POST /autonomy/start`
- `POST /autonomy/stop`
- `GET /video`
- `WS /ws`
