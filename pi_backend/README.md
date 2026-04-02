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

`app.py` initializes controllers, runs startup self-tests (if enabled), and then prints:

- detected Pi IP
- HTTP URL
- WebSocket URL
- video URL

Use the printed HTTP URL in the frontend.

## Edit wiring and tuning

Edit only `config.py`. Main groups:

- backend settings (`HOST`, `PORT`, `WS_PATH`, `VIDEO_PATH`)
- drive motor settings (L298N direction GPIO pins + PCA9685 PWM channels)
- steering servo settings (direct Pi GPIO pin and angle limits)
- camera pan servo settings (direct Pi GPIO pin and angle limits)
- camera settings (enabled flag, source type, index/device path, resolution, fps)
- lidar settings (enabled flag, usb serial port, baud, safety distances)
- drive/autonomy tuning and runtime/debug values

Current default motor values match your wheel test setup:

- `LEFT_MOTOR_FORWARD_PIN = 25`
- `LEFT_MOTOR_REVERSE_PIN = 24`
- `RIGHT_MOTOR_FORWARD_PIN = 17`
- `RIGHT_MOTOR_REVERSE_PIN = 27`
- `LEFT_MOTOR_PWM_CHANNEL = 4`
- `RIGHT_MOTOR_PWM_CHANNEL = 5`
- `FLIP_MOTOR_A = False`
- `FLIP_MOTOR_B = True`

## Frontend connection

Open the dashboard and point it to your Pi backend, for example:

- `http://raspberrypi.local:8000`
- `http://192.168.1.44:8000`

The frontend uses:

- WebSocket telemetry at `/ws`
- camera stream at `/video`
- REST routes for mode changes, waypoint submission, and emergency stop

If needed, check Pi IP manually:

```bash
hostname -I
```

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
