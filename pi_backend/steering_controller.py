from __future__ import annotations

import config
from state import RobotState


class SteeringController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE

    def set_steering(self, angle: float) -> float:
        clamped = round(config.clamp(angle, config.STEERING_MIN_ANGLE, config.STEERING_MAX_ANGLE), 1)
        if self.mock_mode:
            print(f'[STEERING] set angle={clamped}')
        self.state.update(steering_angle=clamped, last_action=f'steering set to {clamped}°')
        return clamped

    def center(self) -> float:
        return self.set_steering(config.STEERING_CENTER_ANGLE)

    def pan_camera(self, angle: float) -> float:
        clamped = round(config.clamp(angle, config.CAMERA_PAN_MIN_ANGLE, config.CAMERA_PAN_MAX_ANGLE), 1)
        if self.mock_mode:
            print(f'[CAMERA] pan angle={clamped}')
        self.state.update(camera_pan_angle=clamped, last_action=f'camera pan set to {clamped}°')
        return clamped
