from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import config
from autonomy_controller import AutonomyController
from lidar_controller import LidarController
from motor_controller import MotorController
from state import RobotState
from steering_controller import SteeringController

BroadcastCallback = Callable[[], Awaitable[None]]


@dataclass
class CommandStep:
    action: str
    value: float | None = None

    @property
    def label(self) -> str:
        return self.action if self.value is None else f'{self.action} {self.value}'


class CommandExecutor:
    def __init__(
        self,
        state: RobotState,
        motor: MotorController,
        steering: SteeringController,
        lidar: LidarController,
        autonomy: AutonomyController,
        broadcast: BroadcastCallback,
    ) -> None:
        self.state = state
        self.motor = motor
        self.steering = steering
        self.lidar = lidar
        self.autonomy = autonomy
        self.broadcast = broadcast
        self.task: asyncio.Task[None] | None = None
        self.queue: list[CommandStep] = []

    def parse_commands(self, payload: str | list[dict[str, Any]]) -> list[CommandStep]:
        if isinstance(payload, str):
            lines = [line.strip() for line in payload.splitlines() if line.strip()]
            return [self._parse_line(line) for line in lines]
        if isinstance(payload, list):
            commands: list[CommandStep] = []
            for item in payload:
                if not isinstance(item, dict) or 'command' not in item:
                    raise ValueError('Each command object must include a command field')
                commands.append(self._parse_line(f"{item['command']} {item['value']}".strip()))
            return commands
        raise ValueError('Commands must be a multi-line string or a list of command objects')

    def _parse_line(self, line: str) -> CommandStep:
        parts = line.split()
        if not parts:
            raise ValueError('Empty command line')
        action = parts[0].lower()
        if action not in {'forward', 'backward', 'left', 'right', 'wait', 'stop'}:
            raise ValueError(f'Unsupported command: {action}')
        if action == 'stop':
            if len(parts) != 1:
                raise ValueError('stop does not take a value')
            return CommandStep(action='stop')
        if len(parts) != 2:
            raise ValueError(f'{action} requires one numeric value')
        try:
            value = float(parts[1])
        except ValueError as exc:
            raise ValueError(f'Invalid numeric value in command: {line}') from exc
        if value < 0:
            raise ValueError('Command values must be non-negative')
        return CommandStep(action=action, value=value)

    async def submit(self, payload: str | list[dict[str, Any]]) -> dict[str, Any]:
        if self.autonomy.task and not self.autonomy.task.done():
            raise ValueError('Stop obstacle avoidance before running waypoint commands')
        if self.task and not self.task.done():
            raise ValueError('A waypoint sequence is already running')
        self.queue = self.parse_commands(payload)
        self.state.update(
            mode='waypoint_by_command',
            waypoint_mode_active=True,
            autonomy_enabled=False,
            command_queue_length=len(self.queue),
            completed_commands=0,
            remaining_commands=len(self.queue),
            current_command=None,
            error=None,
            last_action='waypoint sequence queued',
        )
        self.state.push_event('info', f'Queued {len(self.queue)} waypoint commands')
        self.task = asyncio.create_task(self._run_queue(), name='waypoint-commands')
        await self.broadcast()
        return self.state.snapshot()

    async def stop(self, reason: str = 'waypoint sequence stopped') -> str:
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        self.queue = []
        self.motor.stop(reason)
        self.steering.center()
        self.state.update(
            waypoint_mode_active=False,
            current_command=None,
            command_queue_length=0,
            remaining_commands=0,
        )
        if self.state.snapshot()['mode'] == 'waypoint_by_command':
            self.state.update(mode='idle')
        self.state.push_event('info', reason)
        await self.broadcast()
        return reason

    async def _run_queue(self) -> None:
        completed = 0
        try:
            for index, step in enumerate(self.queue):
                remaining = len(self.queue) - index
                self.state.update(
                    current_command=step.label,
                    command_queue_length=remaining,
                    completed_commands=completed,
                    remaining_commands=remaining,
                    last_action=f'executing {step.label}',
                )
                self.state.push_event('info', f'Executing {step.label}')
                await self.broadcast()
                await self._execute_step(step)
                completed += 1
                self.state.update(completed_commands=completed, remaining_commands=len(self.queue) - completed)
                await self.broadcast()
            self.motor.stop('waypoint sequence complete')
            self.steering.center()
            self.state.update(
                waypoint_mode_active=False,
                current_command=None,
                command_queue_length=0,
                remaining_commands=0,
                mode='idle',
                last_action='waypoint sequence complete',
            )
            self.state.push_event('info', 'Waypoint sequence complete')
            await self.broadcast()
        except asyncio.CancelledError:
            self.motor.stop('waypoint sequence cancelled')
            self.steering.center()
            raise
        except Exception as exc:
            self.motor.emergency_stop(str(exc))
            self.steering.center()
            self.state.update(
                waypoint_mode_active=False,
                mode='idle',
                current_command=None,
                command_queue_length=0,
                remaining_commands=0,
                error=str(exc),
            )
            self.state.push_event('error', str(exc))
            await self.broadcast()
        finally:
            self.task = None
            self.queue = []

    async def _execute_step(self, step: CommandStep) -> None:
        if step.action == 'stop':
            self.motor.stop('waypoint stop command')
            return
        if step.action == 'wait' and step.value is not None:
            await self._wait_with_guard(step.value)
            return
        if step.action in {'forward', 'backward'} and step.value is not None:
            await self._drive_distance(step.action, step.value)
            return
        if step.action in {'left', 'right'} and step.value is not None:
            await self._turn(step.action, step.value)
            return
        raise ValueError(f'Unhandled command: {step.label}')

    async def _drive_distance(self, direction: str, meters: float) -> None:
        if meters == 0:
            return
        speed = config.DEFAULT_DRIVE_SPEED if direction == 'forward' else config.DEFAULT_TURNING_SPEED
        meters_per_second = config.DEFAULT_LINEAR_SPEED_MPS if direction == 'forward' else config.DEFAULT_REVERSE_SPEED_MPS
        duration = meters / meters_per_second
        self.steering.center()
        if direction == 'forward':
            self.motor.forward(speed)
        else:
            self.motor.backward(speed)
        await self._guard_motion(duration, f'obstacle detected during {direction}')
        self.motor.stop(f'{direction} step complete')

    async def _turn(self, direction: str, degrees: float) -> None:
        if degrees == 0:
            return
        target = config.STEERING_MIN_ANGLE if direction == 'left' else config.STEERING_MAX_ANGLE
        duration = degrees / config.TURN_RATE_DEGREES_PER_SECOND
        self.steering.set_steering(target)
        self.motor.forward(config.DEFAULT_TURNING_SPEED)
        await self._guard_motion(duration, f'obstacle detected during turn {direction}')
        self.motor.stop(f'{direction} turn complete')
        self.steering.center()

    async def _wait_with_guard(self, seconds: float) -> None:
        slices = max(1, int(seconds / config.COMMAND_CHECK_INTERVAL_S))
        for _ in range(slices):
            self.lidar.distance_ahead()
            await self.broadcast()
            await asyncio.sleep(config.COMMAND_CHECK_INTERVAL_S)

    async def _guard_motion(self, duration: float, error_message: str) -> None:
        elapsed = 0.0
        while elapsed < duration:
            distance = self.lidar.distance_ahead()
            if distance <= config.CRITICAL_STOP_DISTANCE_M:
                raise RuntimeError(error_message)
            await self.broadcast()
            await asyncio.sleep(config.COMMAND_CHECK_INTERVAL_S)
            elapsed += config.COMMAND_CHECK_INTERVAL_S
