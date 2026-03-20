from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

import config
from lidar_controller import LidarController
from motor_controller import MotorController
from state import RobotState
from steering_controller import SteeringController

BroadcastCallback = Callable[[], Awaitable[None]]


class AutonomyController:
    def __init__(
        self,
        state: RobotState,
        motor: MotorController,
        steering: SteeringController,
        lidar: LidarController,
        broadcast: BroadcastCallback,
    ) -> None:
        self.state = state
        self.motor = motor
        self.steering = steering
        self.lidar = lidar
        self.broadcast = broadcast
        self.task: asyncio.Task[None] | None = None

    async def start(self) -> str:
        if self.task and not self.task.done():
            return 'obstacle avoidance already running'
        self.state.update(mode='obstacle_avoidance', autonomy_enabled=True, waypoint_mode_active=False, error=None)
        self.state.push_event('info', 'Obstacle avoidance started')
        self.task = asyncio.create_task(self._run(), name='obstacle-avoidance')
        await self.broadcast()
        return 'obstacle avoidance started'

    async def stop(self, reason: str = 'obstacle avoidance stopped') -> str:
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        self.motor.stop(reason)
        self.steering.center()
        self.state.update(autonomy_enabled=False)
        if self.state.snapshot()['mode'] == 'obstacle_avoidance':
            self.state.update(mode='idle')
        self.state.push_event('info', reason)
        await self.broadcast()
        return reason

    async def _run(self) -> None:
        try:
            while True:
                distance = self.lidar.distance_ahead()
                if distance <= config.CRITICAL_STOP_DISTANCE_M:
                    self.motor.stop('critical obstacle detected')
                    scan = self.lidar.scan_directions()
                    direction = max(scan, key=scan.get)
                    best_distance = scan[direction]
                    if best_distance <= config.DIRECTION_SCAN_DISTANCE_M:
                        self.state.update(last_action='path blocked, waiting', error='Obstacle too close for safe turn')
                        self.state.push_event('warning', 'Path blocked. Waiting for clearance.')
                        await self.broadcast()
                        await asyncio.sleep(config.TURN_RECOVERY_SECONDS)
                        continue
                    target_angle = {
                        'left': config.STEERING_MIN_ANGLE,
                        'center': config.STEERING_CENTER_ANGLE,
                        'right': config.STEERING_MAX_ANGLE,
                    }[direction]
                    self.steering.set_steering(target_angle)
                    self.motor.forward(config.DEFAULT_TURNING_SPEED)
                    self.state.update(last_action=f'avoiding obstacle by steering {direction}')
                    self.state.push_event('info', f'Obstacle detected. Steering {direction}.')
                    await self.broadcast()
                    await asyncio.sleep(config.TURN_RECOVERY_SECONDS)
                    self.steering.center()
                elif distance <= config.SAFE_FORWARD_DISTANCE_M:
                    scan = self.lidar.scan_directions()
                    direction = 'left' if scan['left'] >= scan['right'] else 'right'
                    target_angle = config.STEERING_MIN_ANGLE if direction == 'left' else config.STEERING_MAX_ANGLE
                    self.steering.set_steering(target_angle)
                    self.motor.forward(config.DEFAULT_TURNING_SPEED)
                    self.state.update(last_action=f'obstacle nearby, biasing {direction}')
                    self.state.push_event('info', f'Obstacle nearby. Biasing {direction}.')
                    await self.broadcast()
                else:
                    self.steering.center()
                    self.motor.forward(config.DEFAULT_DRIVE_SPEED)
                    self.state.update(last_action='path clear, cruising forward')
                    await self.broadcast()
                await asyncio.sleep(config.LIDAR_POLL_INTERVAL_S)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.motor.emergency_stop(f'autonomy failure: {exc}')
            self.state.update(autonomy_enabled=False, mode='idle', error=str(exc))
            self.state.push_event('error', f'Autonomy failure: {exc}')
            await self.broadcast()
