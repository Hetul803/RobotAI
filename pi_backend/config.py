from __future__ import annotations

# backend settings
APP_NAME = 'Autonomous Rover Backend'
HOST = '0.0.0.0'
PORT = 8000
DEBUG = False
MOCK_MODE = True
WS_PATH = '/ws'
VIDEO_PATH = '/video'

# drive motor settings
LEFT_MOTOR_FORWARD_PIN = 25
LEFT_MOTOR_REVERSE_PIN = 24
RIGHT_MOTOR_FORWARD_PIN = 17
RIGHT_MOTOR_REVERSE_PIN = 27
LEFT_MOTOR_PWM_CHANNEL = 4
RIGHT_MOTOR_PWM_CHANNEL = 5
FLIP_MOTOR_A = False
FLIP_MOTOR_B = True
PCA9685_I2C_BUS = 1
PCA9685_I2C_ADDRESS = 0x40
PCA9685_PWM_FREQUENCY_HZ = 1000

# steering servo settings
STEERING_SERVO_MODE = 'pi_gpio'
STEERING_SERVO_GPIO_PIN = 23
STEERING_CENTER_ANGLE = 90
STEERING_MIN_ANGLE = 45
STEERING_MAX_ANGLE = 135

# camera pan servo settings
CAMERA_PAN_SERVO_MODE = 'pi_gpio'
CAMERA_PAN_SERVO_GPIO_PIN = 12
CAMERA_PAN_CENTER_ANGLE = 90
CAMERA_PAN_MIN_ANGLE = 30
CAMERA_PAN_MAX_ANGLE = 150

# camera settings
CAMERA_ENABLED = True
CAMERA_SOURCE_TYPE = 'index'
CAMERA_INDEX = 0
CAMERA_DEVICE_PATH = '/dev/video0'
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 360
VIDEO_FPS = 6
VIDEO_JPEG_QUALITY = 80
VIDEO_STREAM_BOUNDARY = 'frame'

# lidar settings
LIDAR_ENABLED = True
LIDAR_SERIAL_PORT = '/dev/ttyUSB0'
LIDAR_BAUD_RATE = 115200
SAFE_FORWARD_DISTANCE_M = 0.85
CRITICAL_STOP_DISTANCE_M = 0.45
DIRECTION_SCAN_DISTANCE_M = 1.1
TELEMETRY_INTERVAL_S = 0.35
LIDAR_POLL_INTERVAL_S = 0.2

# drive and autonomy tuning
DEFAULT_DRIVE_SPEED = 0.58
DEFAULT_TURNING_SPEED = 0.42
MANUAL_DRIVE_SPEED = 0.46
DEFAULT_LINEAR_SPEED_MPS = 0.65
DEFAULT_REVERSE_SPEED_MPS = 0.45
TURN_RATE_DEGREES_PER_SECOND = 85.0
TURN_RECOVERY_SECONDS = 0.75
COMMAND_CHECK_INTERVAL_S = 0.1

# runtime and debug
STARTUP_SELF_TEST = True
BATTERY_PLACEHOLDER_PERCENT = 86
ROBOT_MODE_OPTIONS = ['idle', 'manual', 'obstacle_avoidance', 'waypoint_by_command']


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def get_public_config() -> dict[str, object]:
    return {
        'app_name': APP_NAME,
        'backend': {
            'host': HOST,
            'port': PORT,
            'debug': DEBUG,
            'mock_mode': MOCK_MODE,
            'ws_path': WS_PATH,
            'video_path': VIDEO_PATH,
        },
        'drive_motors': {
            'left_forward_pin': LEFT_MOTOR_FORWARD_PIN,
            'left_reverse_pin': LEFT_MOTOR_REVERSE_PIN,
            'right_forward_pin': RIGHT_MOTOR_FORWARD_PIN,
            'right_reverse_pin': RIGHT_MOTOR_REVERSE_PIN,
            'left_pwm_channel': LEFT_MOTOR_PWM_CHANNEL,
            'right_pwm_channel': RIGHT_MOTOR_PWM_CHANNEL,
            'flip_motor_a': FLIP_MOTOR_A,
            'flip_motor_b': FLIP_MOTOR_B,
            'pca9685_i2c_bus': PCA9685_I2C_BUS,
            'pca9685_i2c_address': PCA9685_I2C_ADDRESS,
            'pca9685_pwm_frequency_hz': PCA9685_PWM_FREQUENCY_HZ,
        },
        'steering_servo': {
            'mode': STEERING_SERVO_MODE,
            'gpio_pin': STEERING_SERVO_GPIO_PIN,
            'center_angle': STEERING_CENTER_ANGLE,
            'min_angle': STEERING_MIN_ANGLE,
            'max_angle': STEERING_MAX_ANGLE,
        },
        'camera_pan_servo': {
            'mode': CAMERA_PAN_SERVO_MODE,
            'gpio_pin': CAMERA_PAN_SERVO_GPIO_PIN,
            'center_angle': CAMERA_PAN_CENTER_ANGLE,
            'min_angle': CAMERA_PAN_MIN_ANGLE,
            'max_angle': CAMERA_PAN_MAX_ANGLE,
        },
        'camera': {
            'enabled': CAMERA_ENABLED,
            'source_type': CAMERA_SOURCE_TYPE,
            'index': CAMERA_INDEX,
            'device_path': CAMERA_DEVICE_PATH,
            'width': VIDEO_WIDTH,
            'height': VIDEO_HEIGHT,
            'fps': VIDEO_FPS,
            'jpeg_quality': VIDEO_JPEG_QUALITY,
        },
        'lidar': {
            'enabled': LIDAR_ENABLED,
            'serial_port': LIDAR_SERIAL_PORT,
            'baud_rate': LIDAR_BAUD_RATE,
            'safe_forward_distance_m': SAFE_FORWARD_DISTANCE_M,
            'critical_stop_distance_m': CRITICAL_STOP_DISTANCE_M,
            'direction_scan_distance_m': DIRECTION_SCAN_DISTANCE_M,
            'poll_interval_s': LIDAR_POLL_INTERVAL_S,
        },
        'autonomy_tuning': {
            'default_drive_speed': DEFAULT_DRIVE_SPEED,
            'default_turning_speed': DEFAULT_TURNING_SPEED,
            'manual_drive_speed': MANUAL_DRIVE_SPEED,
            'default_linear_speed_mps': DEFAULT_LINEAR_SPEED_MPS,
            'default_reverse_speed_mps': DEFAULT_REVERSE_SPEED_MPS,
            'turn_rate_degrees_per_second': TURN_RATE_DEGREES_PER_SECOND,
            'turn_recovery_seconds': TURN_RECOVERY_SECONDS,
            'command_check_interval_s': COMMAND_CHECK_INTERVAL_S,
            'telemetry_interval_s': TELEMETRY_INTERVAL_S,
        },
        'runtime': {
            'startup_self_test': STARTUP_SELF_TEST,
            'battery_placeholder_percent': BATTERY_PLACEHOLDER_PERCENT,
            'robot_mode_options': ROBOT_MODE_OPTIONS,
        },
    }
