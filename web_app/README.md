# web_app

React + Vite dashboard for the rover backend. It connects to the Pi over REST and WebSocket, shows the camera stream, and exposes manual, obstacle avoidance, and waypoint-by-command controls.

## Install

```bash
cd web_app
npm install
```

## Run

```bash
cd web_app
npm run dev
```

Vite serves the app on `http://localhost:5173` by default.

## Change the backend URL

The dashboard has a backend URL field at the top of the page. The default value is:

- `http://raspberrypi.local:8000`

You can replace it with your Pi IP address, for example:

- `http://192.168.1.44:8000`

## Use it from a laptop or phone on the same Wi-Fi

1. Start the backend on the Raspberry Pi.
2. Start the frontend on your laptop with `npm run dev`.
3. Make sure the laptop, phone, and Pi are on the same Wi-Fi network.
4. Open the laptop's Vite URL in the browser. From a phone, use the laptop IP, such as `http://192.168.1.20:5173`.
5. In the dashboard, point the backend URL field to the Pi.

## Dashboard features

- mode selector for idle, manual, obstacle avoidance, and waypoint-by-command
- emergency stop
- waypoint text area with route submission controls
- live telemetry cards and status strip
- MJPEG camera stream panel
- camera pan slider
- event log driven by backend updates
