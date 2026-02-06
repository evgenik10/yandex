from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Detection:
    label: str
    confidence: float
    camera_id: str


class VisionEngine:
    """Каркас для YOLOv8-nano / MobileNet inference."""

    STOP_CLASSES = {"person", "stop_sign"}

    def infer(self, camera_id: str) -> List[Detection]:
        # Заглушка: сюда подключается реальная модель.
        return []

    def summarize(self, all_detections: Dict[str, List[Detection]]) -> dict:
        flat = [item for sub in all_detections.values() for item in sub]
        must_stop = any(det.label in self.STOP_CLASSES and det.confidence > 0.45 for det in flat)
        return {
            "must_stop": must_stop,
            "detections": [det.__dict__ for det in flat],
        }
