from __future__ import annotations

import importlib
from typing import Any

import config
from state import RobotState


class SteeringController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE
        self.steering_servo: Any | None = None
        self.camera_pan_servo: Any | None = None
        self.steering_ready = False
        self.camera_pan_ready = False

    def initialize(self) -> dict[str, tuple[bool, str]]:
        statuses: dict[str, tuple[bool, str]] = {
            'steering': (True, 'mock mode') if self.mock_mode else (False, 'not initialized'),
            'camera_pan': (True, 'mock mode') if self.mock_mode else (False, 'not initialized'),
        }
        if self.mock_mode:
            self.steering_ready = True
            self.camera_pan_ready = True
            return statuses

        try:
            gpiozero = importlib.import_module('gpiozero')
            if config.STEERING_SERVO_MODE == 'pi_gpio':
                self.steering_servo = gpiozero.AngularServo(
                    config.STEERING_SERVO_GPIO_PIN,
                    min_angle=config.STEERING_MIN_ANGLE,
                    max_angle=config.STEERING_MAX_ANGLE,
                )
                self.steering_ready = True
                statuses['steering'] = (True, 'hardware ready')
            else:
                statuses['steering'] = (False, f'unsupported mode: {config.STEERING_SERVO_MODE}')
        except Exception as exc:
            self.steering_ready = False
            statuses['steering'] = (False, str(exc))

        try:
            gpiozero = importlib.import_module('gpiozero')
            if config.CAMERA_PAN_SERVO_MODE == 'pi_gpio':
                self.camera_pan_servo = gpiozero.AngularServo(
                    config.CAMERA_PAN_SERVO_GPIO_PIN,
                    min_angle=config.CAMERA_PAN_MIN_ANGLE,
                    max_angle=config.CAMERA_PAN_MAX_ANGLE,
                )
                self.camera_pan_ready = True
                statuses['camera_pan'] = (True, 'hardware ready')
            else:
                statuses['camera_pan'] = (False, f'unsupported mode: {config.CAMERA_PAN_SERVO_MODE}')
        except Exception as exc:
            self.camera_pan_ready = False
            statuses['camera_pan'] = (False, str(exc))

        return statuses

    def set_steering(self, angle: float) -> float:
        clamped = round(config.clamp(angle, config.STEERING_MIN_ANGLE, config.STEERING_MAX_ANGLE), 1)
        if self.mock_mode:
            print(f'[STEERING] set angle={clamped}')
        if self.steering_ready and self.steering_servo is not None:
            self.steering_servo.angle = clamped
        self.state.update(steering_angle=clamped, last_action=f'steering set to {clamped}°')
        return clamped

    def center(self) -> float:
        return self.set_steering(config.STEERING_CENTER_ANGLE)

    def pan_camera(self, angle: float) -> float:
        clamped = round(config.clamp(angle, config.CAMERA_PAN_MIN_ANGLE, config.CAMERA_PAN_MAX_ANGLE), 1)
        if self.mock_mode:
            print(f'[CAMERA PAN] angle={clamped}')
        if self.camera_pan_ready and self.camera_pan_servo is not None:
            self.camera_pan_servo.angle = clamped
        self.state.update(camera_pan_angle=clamped, last_action=f'camera pan set to {clamped}°')
        return clamped
