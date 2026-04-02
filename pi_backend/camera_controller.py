from __future__ import annotations

import importlib
import io
import time
from typing import Any, Iterator

from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw

import config
from state import RobotState


class CameraController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE
        self.enabled = config.CAMERA_ENABLED
        self.capture: Any | None = None

    def initialize(self) -> tuple[bool, str]:
        if not self.enabled:
            self.state.update(camera_status='disabled')
            return True, 'disabled by config'
        if self.mock_mode:
            self.state.update(camera_status='mock stream')
            return True, 'mock mode'
        try:
            cv2 = importlib.import_module('cv2')
            source = config.CAMERA_INDEX if config.CAMERA_SOURCE_TYPE == 'index' else config.CAMERA_DEVICE_PATH
            self.capture = cv2.VideoCapture(source)
            if not self.capture.isOpened():
                raise RuntimeError(f'cannot open camera source: {source}')
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.VIDEO_WIDTH)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.VIDEO_HEIGHT)
            self.capture.set(cv2.CAP_PROP_FPS, config.VIDEO_FPS)
            self.state.update(camera_status='hardware stream ready')
            return True, 'hardware ready'
        except Exception as exc:
            if config.MOCK_MODE:
                self.state.update(camera_status='mock fallback')
                return True, f'mock fallback: {exc}'
            self.state.update(camera_status='failed')
            return False, str(exc)

    def _build_overlay_frame(self) -> bytes:
        snapshot = self.state.snapshot()
        image = Image.new('RGB', (config.VIDEO_WIDTH, config.VIDEO_HEIGHT), color=(9, 16, 34))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((18, 18, config.VIDEO_WIDTH - 18, config.VIDEO_HEIGHT - 18), radius=18, outline=(72, 123, 255), width=3)
        draw.text((34, 34), 'Rover camera', fill=(235, 240, 255))
        draw.text((34, 74), f"mode: {snapshot['mode']}", fill=(170, 196, 255))
        draw.text((34, 102), f"speed: {snapshot['speed']}", fill=(170, 196, 255))
        draw.text((34, 130), f"obstacle: {snapshot['obstacle_distance']} m", fill=(170, 196, 255))
        draw.text((34, 158), f"steering: {snapshot['steering_angle']}°", fill=(170, 196, 255))
        draw.text((34, 186), f"camera pan: {snapshot['camera_pan_angle']}°", fill=(170, 196, 255))
        draw.text((34, 214), f"last action: {snapshot['last_action']}", fill=(255, 216, 141))
        if snapshot['error']:
            draw.text((34, 252), f"error: {snapshot['error']}", fill=(255, 128, 128))
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=config.VIDEO_JPEG_QUALITY)
        return buffer.getvalue()

    def _read_camera_frame(self) -> bytes | None:
        if self.capture is None:
            return None
        try:
            cv2 = importlib.import_module('cv2')
            ok, frame = self.capture.read()
            if not ok:
                return None
            ok, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), config.VIDEO_JPEG_QUALITY])
            if not ok:
                return None
            return bytes(encoded)
        except Exception:
            return None

    def stream(self) -> Iterator[bytes]:
        interval = 1 / max(config.VIDEO_FPS, 1)
        while True:
            frame = self._read_camera_frame() if not self.mock_mode and self.enabled else None
            if frame is None:
                frame = self._build_overlay_frame()
            yield (
                f'--{config.VIDEO_STREAM_BOUNDARY}\r\n'
                'Content-Type: image/jpeg\r\n\r\n'
            ).encode('utf-8') + frame + b'\r\n'
            time.sleep(interval)

    def response(self) -> StreamingResponse:
        return StreamingResponse(
            self.stream(),
            media_type=f'multipart/x-mixed-replace; boundary={config.VIDEO_STREAM_BOUNDARY}',
        )
