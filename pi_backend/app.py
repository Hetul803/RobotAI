"""FastAPI backend server for Raspberry Pi robot control."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import config
import motor_controller as motor

app = FastAPI(title=config.APP_NAME)


@app.get("/")
async def health() -> dict[str, str]:
    """Health check route."""
    return {"status": "ok", "service": config.APP_NAME}


def execute_command(command: str, payload: dict[str, Any]) -> str:
    """Map command strings to motor/servo actions."""
    if command == "forward":
        return motor.forward()
    if command == "backward":
        return motor.backward()
    if command == "left":
        return motor.left()
    if command == "right":
        return motor.right()
    if command == "stop":
        return motor.stop()
    if command == "servo_pan":
        return motor.servo_pan(payload.get("value", 90))
    if command == "servo_tilt":
        return motor.servo_tilt(payload.get("value", 90))
    raise ValueError(f"Unsupported command: {command}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time robot control."""
    await websocket.accept()
    last_action = "connected"

    await websocket.send_json(
        {
            "status": "connected",
            "last_action": last_action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "status": "error",
                        "last_action": last_action,
                        "message": "Invalid JSON payload",
                    }
                )
                continue

            command = payload.get("command")
            if not isinstance(command, str):
                await websocket.send_json(
                    {
                        "status": "error",
                        "last_action": last_action,
                        "message": "'command' must be a string",
                    }
                )
                continue

            try:
                last_action = execute_command(command, payload)
                await websocket.send_json(
                    {
                        "status": "ok",
                        "last_action": last_action,
                        "received": payload,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except ValueError as exc:
                await websocket.send_json(
                    {
                        "status": "error",
                        "last_action": last_action,
                        "message": str(exc),
                    }
                )
    except WebSocketDisconnect:
        motor.stop()
        print("[WS] Client disconnected. Safety stop executed.")


if __name__ == "__main__":
    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
