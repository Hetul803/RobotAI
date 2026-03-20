from __future__ import annotations

import io
import time
from typing import Iterator

from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw

import config
from state import RobotState


class CameraController:
    def __init__(self, state: RobotState) -> None:
        self.state = state
        self.mock_mode = config.MOCK_MODE
        self.state.update(camera_status='mock stream' if self.mock_mode else 'ready')

    def _build_frame(self) -> bytes:
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
        draw.line((config.VIDEO_WIDTH // 2, 40, config.VIDEO_WIDTH // 2, config.VIDEO_HEIGHT - 40), fill=(62, 97, 196), width=2)
        draw.line((60, config.VIDEO_HEIGHT // 2, config.VIDEO_WIDTH - 60, config.VIDEO_HEIGHT // 2), fill=(62, 97, 196), width=2)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=config.VIDEO_JPEG_QUALITY)
        return buffer.getvalue()

    def stream(self) -> Iterator[bytes]:
        interval = 1 / max(config.VIDEO_FPS, 1)
        while True:
            frame = self._build_frame()
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
