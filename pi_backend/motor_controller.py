"""Mock motor and servo controller.

Replace the print statements with real Raspberry Pi GPIO code when deploying to hardware.
"""

from __future__ import annotations


def forward() -> str:
    print("[MOTOR] Moving forward")
    return "forward"


def backward() -> str:
    print("[MOTOR] Moving backward")
    return "backward"


def left() -> str:
    print("[MOTOR] Turning left")
    return "left"


def right() -> str:
    print("[MOTOR] Turning right")
    return "right"


def stop() -> str:
    print("[MOTOR] Stopping robot")
    return "stop"


def servo_pan(value: int) -> str:
    clamped = max(0, min(180, int(value)))
    print(f"[SERVO] Pan set to {clamped}")
    return f"servo_pan:{clamped}"


def servo_tilt(value: int) -> str:
    clamped = max(0, min(180, int(value)))
    print(f"[SERVO] Tilt set to {clamped}")
    return f"servo_tilt:{clamped}"
