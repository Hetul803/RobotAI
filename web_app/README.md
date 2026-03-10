# Robot Web App (`web_app`)

This is a React + Vite web control console for a Raspberry Pi robot backend.

## Install

```bash
cd web_app
npm install
```

## Run development server

```bash
cd web_app
npm run dev
```

The app usually runs at `http://localhost:5173`.

## Change Raspberry Pi address

In the app UI, edit the WebSocket URL field.

Default value:

- `ws://raspberrypi.local:8000/ws`

Alternative:

- `ws://<pi-ip>:8000/ws`

## Use from laptop or phone browser on same Wi-Fi

1. Start backend on the Raspberry Pi.
2. Start frontend with `npm run dev` on your laptop.
3. Ensure phone/laptop/Pi are on the same Wi-Fi network.
4. Open the laptop's frontend URL from phone browser (you may need laptop local IP like `http://192.168.1.x:5173`).
5. In the app, set WebSocket URL to Pi address and press **Connect**.

## Features in UI

- Dark futuristic responsive control dashboard
- Connect/disconnect to backend WebSocket
- Movement commands: forward, backward, left, right, stop
- Servo controls: pan and tilt sliders
- Placeholder telemetry cards (battery, distance, mode)
- Live command and response log panel
