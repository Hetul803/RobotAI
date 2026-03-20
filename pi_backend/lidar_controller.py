from __future__ import annotations

import math
import time

import config
from state import RobotState


class LidarController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE
        self.started_at = time.monotonic()

    def _mock_distance(self, phase_offset: float = 0.0) -> float:
        elapsed = time.monotonic() - self.started_at + phase_offset
        baseline = 1.45 + math.sin(elapsed * 0.35) * 0.7
        pulse = 0.3 if int(elapsed) % 12 < 8 else -0.55
        distance = round(max(0.25, baseline + pulse), 2)
        return distance

    def distance_ahead(self) -> float:
        distance = self._mock_distance() if self.mock_mode else self._mock_distance()
        self.state.update(obstacle_distance=distance, lidar_status='streaming')
        return distance

    def scan_directions(self) -> dict[str, float]:
        if self.mock_mode:
            scan = {
                'left': self._mock_distance(0.9),
                'center': self._mock_distance(0.0),
                'right': self._mock_distance(1.8),
            }
        else:
            scan = {'left': self.distance_ahead(), 'center': self.distance_ahead(), 'right': self.distance_ahead()}
        self.state.update(obstacle_distance=scan['center'], lidar_status='scan complete')
        return scan
