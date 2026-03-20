from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

import config
from autonomy_controller import AutonomyController
from camera_controller import CameraController
from command_executor import CommandExecutor
from lidar_controller import LidarController
from motor_controller import MotorController
from state import RobotState
from steering_controller import SteeringController


class ModeRequest(BaseModel):
    mode: str


class WaypointRequest(BaseModel):
    commands: str | list[dict[str, Any]] = Field(..., description='Multi-line commands or command objects')


class WebSocketHub:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.clients.add(websocket)
        self.state.update(connected=True)

    async def disconnect(self, websocket: WebSocket) -> None:
        self.clients.discard(websocket)
        self.state.update(connected=bool(self.clients))

    async def broadcast(self, payload: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for client in list(self.clients):
            try:
                await client.send_json(payload)
            except Exception:
                stale.append(client)
        for client in stale:
            self.clients.discard(client)
        self.state.update(connected=bool(self.clients))


state = RobotState()
hub = WebSocketHub(state)
motor = MotorController(state)
steering = SteeringController(state)
lidar = LidarController(state)
camera = CameraController(state)


async def broadcast_state() -> None:
    payload = state.snapshot()
    payload['timestamp'] = datetime.now(timezone.utc).isoformat()
    await hub.broadcast(payload)


autonomy = AutonomyController(state, motor, steering, lidar, broadcast_state)
executor = CommandExecutor(state, motor, steering, lidar, autonomy, broadcast_state)
app = FastAPI(title=config.APP_NAME)
telemetry_task: asyncio.Task[None] | None = None


@app.on_event('startup')
async def startup_event() -> None:
    global telemetry_task

    async def telemetry_loop() -> None:
        while True:
            lidar.distance_ahead()
            await broadcast_state()
            await asyncio.sleep(config.TELEMETRY_INTERVAL_S)

    telemetry_task = asyncio.create_task(telemetry_loop(), name='telemetry-loop')


@app.on_event('shutdown')
async def shutdown_event() -> None:
    global telemetry_task
    motor.stop('backend shutdown')
    steering.center()
    if telemetry_task:
        telemetry_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await telemetry_task
        telemetry_task = None
    await autonomy.stop('backend shutdown')
    await executor.stop('backend shutdown')


@app.get('/')
async def health() -> dict[str, Any]:
    return {
        'status': 'ok',
        'service': config.APP_NAME,
        'mode': state.snapshot()['mode'],
        'mock_mode': config.MOCK_MODE,
    }


@app.get('/state')
async def get_state() -> dict[str, Any]:
    return state.snapshot()


@app.get('/config')
async def get_config() -> dict[str, Any]:
    return config.get_public_config()


@app.post('/mode')
async def set_mode(request: ModeRequest) -> dict[str, Any]:
    mode = request.mode.strip().lower()
    if mode not in config.ROBOT_MODE_OPTIONS:
        raise HTTPException(status_code=400, detail='Unsupported mode')
    if mode == 'obstacle_avoidance':
        await executor.stop('switching to obstacle avoidance')
        await autonomy.start()
    elif mode == 'waypoint_by_command':
        state.update(mode=mode, waypoint_mode_active=False, autonomy_enabled=False, last_action='waypoint mode armed')
    else:
        await autonomy.stop(f'switching to {mode}')
        await executor.stop(f'switching to {mode}')
        state.update(mode=mode, autonomy_enabled=False, waypoint_mode_active=False, error=None)
    state.push_event('info', f'Mode set to {mode}')
    await broadcast_state()
    return state.snapshot()


@app.post('/stop')
async def emergency_stop() -> dict[str, Any]:
    await autonomy.stop('emergency stop')
    await executor.stop('emergency stop')
    motor.emergency_stop('emergency stop')
    steering.center()
    state.update(mode='idle', autonomy_enabled=False, waypoint_mode_active=False, current_command=None, command_queue_length=0, remaining_commands=0)
    state.push_event('warning', 'Emergency stop issued')
    await broadcast_state()
    return state.snapshot()


@app.post('/waypoints')
async def submit_waypoints(request: WaypointRequest) -> dict[str, Any]:
    try:
        snapshot = await executor.submit(request.commands)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return snapshot


@app.post('/autonomy/start')
async def start_autonomy() -> dict[str, Any]:
    await executor.stop('switching to obstacle avoidance')
    await autonomy.start()
    return state.snapshot()


@app.post('/autonomy/stop')
async def stop_autonomy() -> dict[str, Any]:
    await autonomy.stop('obstacle avoidance stopped from api')
    return state.snapshot()


@app.get('/video')
async def video_stream() -> Any:
    return camera.response()


async def handle_ws_message(payload: dict[str, Any]) -> None:
    command = str(payload.get('command', '')).strip().lower()
    if not command:
        raise ValueError('Missing command field')
    if command == 'forward':
        state.update(mode='manual', autonomy_enabled=False, waypoint_mode_active=False)
        steering.center()
        motor.forward(config.MANUAL_DRIVE_SPEED)
    elif command == 'backward':
        state.update(mode='manual', autonomy_enabled=False, waypoint_mode_active=False)
        steering.center()
        motor.backward(config.MANUAL_DRIVE_SPEED)
    elif command == 'left':
        state.update(mode='manual', autonomy_enabled=False, waypoint_mode_active=False)
        steering.set_steering(config.STEERING_MIN_ANGLE)
        motor.forward(config.MANUAL_DRIVE_SPEED)
    elif command == 'right':
        state.update(mode='manual', autonomy_enabled=False, waypoint_mode_active=False)
        steering.set_steering(config.STEERING_MAX_ANGLE)
        motor.forward(config.MANUAL_DRIVE_SPEED)
    elif command == 'stop':
        motor.stop('manual stop')
        steering.center()
    elif command == 'camera_pan':
        steering.pan_camera(float(payload.get('value', config.CAMERA_PAN_CENTER_ANGLE)))
    elif command == 'mode':
        await set_mode(ModeRequest(mode=str(payload.get('value', 'idle'))))
    elif command == 'autonomy_start':
        await start_autonomy()
    elif command == 'autonomy_stop':
        await stop_autonomy()
    else:
        raise ValueError(f'Unsupported command: {command}')
    state.clear_error()
    state.push_event('info', f'WebSocket command: {command}')
    await broadcast_state()


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    await broadcast_state()
    try:
        while True:
            payload = await websocket.receive_json()
            try:
                await handle_ws_message(payload)
            except ValueError as exc:
                state.update(error=str(exc), last_action='websocket command rejected')
                state.push_event('error', str(exc))
                await broadcast_state()
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
        await autonomy.stop('websocket disconnected')
        await executor.stop('websocket disconnected')
        motor.stop('websocket disconnected')
        steering.center()
        state.push_event('warning', 'WebSocket disconnected, rover stopped')
        await broadcast_state()
    except Exception as exc:
        await hub.disconnect(websocket)
        motor.emergency_stop(f'websocket failure: {exc}')
        steering.center()
        state.push_event('error', f'WebSocket failure: {exc}')
        await broadcast_state()


if __name__ == '__main__':
    uvicorn.run('app:app', host=config.HOST, port=config.PORT, reload=config.DEBUG)
