from __future__ import annotations

import importlib
import math
import time
from typing import Any

import config
from state import RobotState


class LidarController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE
        self.enabled = config.LIDAR_ENABLED
        self.started_at = time.monotonic()
        self.serial_port: Any | None = None

    def initialize(self) -> tuple[bool, str]:
        if not self.enabled:
            self.state.update(lidar_status='disabled')
            return True, 'disabled by config'
        if self.mock_mode:
            self.state.update(lidar_status='mock stream')
            return True, 'mock mode'
        try:
            serial = importlib.import_module('serial')
            self.serial_port = serial.Serial(config.LIDAR_SERIAL_PORT, config.LIDAR_BAUD_RATE, timeout=0.2)
            self.state.update(lidar_status='serial ready')
            return True, 'hardware ready'
        except Exception as exc:
            if config.MOCK_MODE:
                self.state.update(lidar_status='mock fallback')
                return True, f'mock fallback: {exc}'
            self.state.update(lidar_status='failed')
            return False, str(exc)

    def _mock_distance(self, phase_offset: float = 0.0) -> float:
        elapsed = time.monotonic() - self.started_at + phase_offset
        baseline = 1.45 + math.sin(elapsed * 0.35) * 0.7
        pulse = 0.3 if int(elapsed) % 12 < 8 else -0.55
        return round(max(0.25, baseline + pulse), 2)

    def _read_distance_hardware(self) -> float | None:
        if self.serial_port is None:
            return None
        try:
            raw = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
            if not raw:
                return None
            distance = float(raw)
            return round(max(0.0, distance), 2)
        except Exception:
            return None

    def distance_ahead(self) -> float:
        if not self.enabled:
            distance = 9.99
            self.state.update(obstacle_distance=distance, lidar_status='disabled')
            return distance

        distance = self._mock_distance() if self.mock_mode else self._read_distance_hardware()
        if distance is None:
            distance = self._mock_distance()
            status = 'mock fallback'
        else:
            status = 'streaming'
        self.state.update(obstacle_distance=distance, lidar_status=status)
        return distance

    def scan_directions(self) -> dict[str, float]:
        scan = {
            'left': self._mock_distance(0.9) if self.mock_mode else self.distance_ahead(),
            'center': self.distance_ahead(),
            'right': self._mock_distance(1.8) if self.mock_mode else self.distance_ahead(),
        }
        self.state.update(obstacle_distance=scan['center'], lidar_status='scan complete')
        return scan
