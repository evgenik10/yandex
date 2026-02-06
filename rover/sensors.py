from dataclasses import dataclass


@dataclass
class ObstacleReading:
    distance_cm: float
    is_blocked: bool


class UltrasonicSensor:
    def __init__(self, stop_distance_cm: float = 70.0):
        self.stop_distance_cm = stop_distance_cm
        self._distance_cm = 120.0

    def read_distance(self) -> ObstacleReading:
        is_blocked = self._distance_cm <= self.stop_distance_cm
        return ObstacleReading(distance_cm=self._distance_cm, is_blocked=is_blocked)

    def set_simulated_distance(self, distance_cm: float) -> None:
        self._distance_cm = distance_cm
