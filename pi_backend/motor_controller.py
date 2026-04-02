from __future__ import annotations

import importlib
from typing import Any

import config
from state import RobotState


class MotorController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE
        self.hardware_ready = False
        self.left_forward: Any | None = None
        self.left_reverse: Any | None = None
        self.right_forward: Any | None = None
        self.right_reverse: Any | None = None
        self.left_pwm_channel: Any | None = None
        self.right_pwm_channel: Any | None = None
        self.pca: Any | None = None

    def initialize(self) -> tuple[bool, str]:
        if self.mock_mode:
            self.hardware_ready = True
            return True, 'mock mode'
        try:
            gpiozero = importlib.import_module('gpiozero')
            board = importlib.import_module('board')
            busio = importlib.import_module('busio')
            adafruit_pca9685 = importlib.import_module('adafruit_pca9685')

            self.left_forward = gpiozero.DigitalOutputDevice(config.LEFT_MOTOR_FORWARD_PIN)
            self.left_reverse = gpiozero.DigitalOutputDevice(config.LEFT_MOTOR_REVERSE_PIN)
            self.right_forward = gpiozero.DigitalOutputDevice(config.RIGHT_MOTOR_FORWARD_PIN)
            self.right_reverse = gpiozero.DigitalOutputDevice(config.RIGHT_MOTOR_REVERSE_PIN)

            scl = getattr(board, f'SCL_{config.PCA9685_I2C_BUS}', board.SCL)
            sda = getattr(board, f'SDA_{config.PCA9685_I2C_BUS}', board.SDA)
            i2c = busio.I2C(scl, sda)
            self.pca = adafruit_pca9685.PCA9685(i2c, address=config.PCA9685_I2C_ADDRESS)
            self.pca.frequency = config.PCA9685_PWM_FREQUENCY_HZ
            self.left_pwm_channel = self.pca.channels[config.LEFT_MOTOR_PWM_CHANNEL]
            self.right_pwm_channel = self.pca.channels[config.RIGHT_MOTOR_PWM_CHANNEL]
            self._write_pwm(self.left_pwm_channel, 0.0)
            self._write_pwm(self.right_pwm_channel, 0.0)
            self.hardware_ready = True
            return True, 'hardware ready'
        except Exception as exc:
            self.hardware_ready = False
            return False, str(exc)

    def _write_pwm(self, channel: Any | None, speed: float) -> None:
        if channel is None:
            return
        duty_cycle = int(config.clamp(speed, 0.0, 1.0) * 65535)
        channel.duty_cycle = duty_cycle

    def _set_direction(self, left_forward: bool, right_forward: bool) -> None:
        if self.mock_mode or not self.hardware_ready:
            return
        left_forward = not left_forward if config.FLIP_MOTOR_A else left_forward
        right_forward = not right_forward if config.FLIP_MOTOR_B else right_forward
        if left_forward:
            self.left_forward.on()
            self.left_reverse.off()
        else:
            self.left_forward.off()
            self.left_reverse.on()
        if right_forward:
            self.right_forward.on()
            self.right_reverse.off()
        else:
            self.right_forward.off()
            self.right_reverse.on()

    def _apply(self, direction: str, speed: float, action: str) -> str:
        speed = round(config.clamp(speed, 0.0, 1.0), 2)
        if direction == 'forward':
            self._set_direction(left_forward=True, right_forward=True)
        elif direction == 'backward':
            self._set_direction(left_forward=False, right_forward=False)
        self._write_pwm(self.left_pwm_channel, speed)
        self._write_pwm(self.right_pwm_channel, speed)
        if self.mock_mode:
            print(f'[MOTOR] {action} | direction={direction} speed={speed}')
        self.state.update(speed=speed, drive_direction=direction, last_action=action, error=None)
        return action

    def forward(self, speed: float | None = None) -> str:
        return self._apply('forward', speed or config.DEFAULT_DRIVE_SPEED, 'driving forward')

    def backward(self, speed: float | None = None) -> str:
        return self._apply('backward', speed or config.DEFAULT_TURNING_SPEED, 'driving backward')

    def stop(self, reason: str = 'stopped') -> str:
        self._write_pwm(self.left_pwm_channel, 0.0)
        self._write_pwm(self.right_pwm_channel, 0.0)
        if not self.mock_mode and self.hardware_ready:
            self.left_forward.off()
            self.left_reverse.off()
            self.right_forward.off()
            self.right_reverse.off()
        if self.mock_mode:
            print(f'[MOTOR] stop | reason={reason}')
        self.state.update(speed=0.0, drive_direction='stopped', last_action=reason)
        return reason

    def emergency_stop(self, reason: str = 'emergency stop') -> str:
        self.stop(reason)
        if self.mock_mode:
            print(f'[MOTOR] emergency_stop | reason={reason}')
        self.state.update(error=reason)
        return reason
