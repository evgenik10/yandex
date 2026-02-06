from dataclasses import dataclass
from typing import Dict


@dataclass
class CameraFrame:
    camera_id: str
    stream_url: str


class CameraHub:
    """Управление 4 USB-камерами."""

    def __init__(self) -> None:
        self.cameras = {
            "front": CameraFrame("front", "/streams/front"),
            "rear": CameraFrame("rear", "/streams/rear"),
            "left": CameraFrame("left", "/streams/left"),
            "right": CameraFrame("right", "/streams/right"),
        }

    def list_streams(self) -> Dict[str, str]:
        return {name: frame.stream_url for name, frame in self.cameras.items()}
