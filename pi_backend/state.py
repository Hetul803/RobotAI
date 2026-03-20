from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any

import config


@dataclass
class RobotSnapshot:
    mode: str = 'idle'
    connected: bool = False
    autonomy_enabled: bool = False
    waypoint_mode_active: bool = False
    current_command: str | None = None
    command_queue_length: int = 0
    completed_commands: int = 0
    remaining_commands: int = 0
    obstacle_distance: float | None = None
    steering_angle: float = config.STEERING_CENTER_ANGLE
    camera_pan_angle: float = config.CAMERA_PAN_CENTER_ANGLE
    speed: float = 0.0
    drive_direction: str = 'stopped'
    camera_status: str = 'ready'
    lidar_status: str = 'ready'
    battery_level: int = config.BATTERY_PLACEHOLDER_PERCENT
    last_action: str = 'idle'
    error: str | None = None
    recent_events: list[dict[str, Any]] = field(default_factory=list)


class RobotState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._snapshot = RobotSnapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(asdict(self._snapshot))

    def update(self, **values: Any) -> dict[str, Any]:
        with self._lock:
            for key, value in values.items():
                if hasattr(self._snapshot, key):
                    setattr(self._snapshot, key, value)
            return deepcopy(asdict(self._snapshot))

    def set_mode(self, mode: str) -> dict[str, Any]:
        if mode not in config.ROBOT_MODE_OPTIONS:
            raise ValueError(f'Unsupported mode: {mode}')
        return self.update(mode=mode)

    def push_event(self, level: str, message: str) -> dict[str, Any]:
        with self._lock:
            self._snapshot.recent_events.insert(0, {'level': level, 'message': message})
            self._snapshot.recent_events = self._snapshot.recent_events[:40]
            return deepcopy(asdict(self._snapshot))

    def clear_error(self) -> dict[str, Any]:
        return self.update(error=None)
