from __future__ import annotations

APP_NAME = 'Autonomous Rover Backend'
HOST = '0.0.0.0'
PORT = 8000
DEBUG = False
MOCK_MODE = True

LEFT_MOTOR_FORWARD_PIN = 17
LEFT_MOTOR_REVERSE_PIN = 27
RIGHT_MOTOR_FORWARD_PIN = 22
RIGHT_MOTOR_REVERSE_PIN = 23
LEFT_MOTOR_PWM_PIN = 18
RIGHT_MOTOR_PWM_PIN = 13
FRONT_STEERING_SERVO_CHANNEL = 0
CAMERA_PAN_SERVO_CHANNEL = 1

STEERING_CENTER_ANGLE = 90
STEERING_MIN_ANGLE = 55
STEERING_MAX_ANGLE = 125
CAMERA_PAN_CENTER_ANGLE = 90
CAMERA_PAN_MIN_ANGLE = 30
CAMERA_PAN_MAX_ANGLE = 150

LIDAR_SERIAL_PORT = '/dev/ttyUSB0'
LIDAR_BAUD_RATE = 115200
SAFE_FORWARD_DISTANCE_M = 0.85
CRITICAL_STOP_DISTANCE_M = 0.45
DIRECTION_SCAN_DISTANCE_M = 1.1
TELEMETRY_INTERVAL_S = 0.35
LIDAR_POLL_INTERVAL_S = 0.2

DEFAULT_DRIVE_SPEED = 0.58
DEFAULT_TURNING_SPEED = 0.42
MANUAL_DRIVE_SPEED = 0.46
DEFAULT_LINEAR_SPEED_MPS = 0.65
DEFAULT_REVERSE_SPEED_MPS = 0.45
TURN_RATE_DEGREES_PER_SECOND = 85.0
TURN_RECOVERY_SECONDS = 0.75
COMMAND_CHECK_INTERVAL_S = 0.1

VIDEO_WIDTH = 640
VIDEO_HEIGHT = 360
VIDEO_FPS = 6
VIDEO_JPEG_QUALITY = 80
VIDEO_STREAM_BOUNDARY = 'frame'

BATTERY_PLACEHOLDER_PERCENT = 86
ROBOT_MODE_OPTIONS = ['idle', 'manual', 'obstacle_avoidance', 'waypoint_by_command']


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def get_public_config() -> dict[str, object]:
    return {
        'app_name': APP_NAME,
        'mock_mode': MOCK_MODE,
        'host': HOST,
        'port': PORT,
        'motor_pins': {
            'left_forward': LEFT_MOTOR_FORWARD_PIN,
            'left_reverse': LEFT_MOTOR_REVERSE_PIN,
            'right_forward': RIGHT_MOTOR_FORWARD_PIN,
            'right_reverse': RIGHT_MOTOR_REVERSE_PIN,
            'left_pwm': LEFT_MOTOR_PWM_PIN,
            'right_pwm': RIGHT_MOTOR_PWM_PIN,
        },
        'servo_channels': {
            'front_steering': FRONT_STEERING_SERVO_CHANNEL,
            'camera_pan': CAMERA_PAN_SERVO_CHANNEL,
        },
        'steering': {
            'center': STEERING_CENTER_ANGLE,
            'min': STEERING_MIN_ANGLE,
            'max': STEERING_MAX_ANGLE,
        },
        'camera_pan': {
            'center': CAMERA_PAN_CENTER_ANGLE,
            'min': CAMERA_PAN_MIN_ANGLE,
            'max': CAMERA_PAN_MAX_ANGLE,
        },
        'lidar': {
            'serial_port': LIDAR_SERIAL_PORT,
            'baud_rate': LIDAR_BAUD_RATE,
            'safe_forward_distance_m': SAFE_FORWARD_DISTANCE_M,
            'critical_stop_distance_m': CRITICAL_STOP_DISTANCE_M,
            'direction_scan_distance_m': DIRECTION_SCAN_DISTANCE_M,
        },
        'drive': {
            'default_drive_speed': DEFAULT_DRIVE_SPEED,
            'default_turning_speed': DEFAULT_TURNING_SPEED,
            'manual_drive_speed': MANUAL_DRIVE_SPEED,
            'default_linear_speed_mps': DEFAULT_LINEAR_SPEED_MPS,
            'default_reverse_speed_mps': DEFAULT_REVERSE_SPEED_MPS,
            'turn_rate_degrees_per_second': TURN_RATE_DEGREES_PER_SECOND,
        },
        'video': {
            'width': VIDEO_WIDTH,
            'height': VIDEO_HEIGHT,
            'fps': VIDEO_FPS,
            'jpeg_quality': VIDEO_JPEG_QUALITY,
        },
    }
