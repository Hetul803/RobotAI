from __future__ import annotations

import config
from state import RobotState


class MotorController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE

    def _apply(self, direction: str, speed: float, action: str) -> str:
        speed = round(config.clamp(speed, 0.0, 1.0), 2)
        if self.mock_mode:
            print(f'[MOTOR] {action} | direction={direction} speed={speed}')
        self.state.update(speed=speed, drive_direction=direction, last_action=action, error=None)
        return action

    def forward(self, speed: float | None = None) -> str:
        return self._apply('forward', speed or config.DEFAULT_DRIVE_SPEED, 'driving forward')

    def backward(self, speed: float | None = None) -> str:
        return self._apply('backward', speed or config.DEFAULT_TURNING_SPEED, 'driving backward')

    def stop(self, reason: str = 'stopped') -> str:
        if self.mock_mode:
            print(f'[MOTOR] stop | reason={reason}')
        self.state.update(speed=0.0, drive_direction='stopped', last_action=reason)
        return reason

    def emergency_stop(self, reason: str = 'emergency stop') -> str:
        if self.mock_mode:
            print(f'[MOTOR] emergency_stop | reason={reason}')
        self.state.update(speed=0.0, drive_direction='stopped', last_action=reason, error=reason)
        return reason
