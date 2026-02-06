from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from typing import List, Tuple


class RoverMode(str, Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class PDDState(str, Enum):
    ON_TRACK = "ON_TRACK"
    OFF_TRACK = "OFF_TRACK"
    RETURNING = "RETURNING"
    STOP = "STOP"


@dataclass
class RouteState:
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    current_idx: int = 0


class Navigator:
    def __init__(self, lane_tolerance_m: float = 3.0):
        self.mode = RoverMode.MANUAL
        self.pdd_state = PDDState.STOP
        self.route = RouteState()
        self.lane_tolerance_m = lane_tolerance_m

    def set_route(self, waypoints: List[Tuple[float, float]]) -> None:
        self.route = RouteState(waypoints=waypoints, current_idx=0)
        self.mode = RoverMode.AUTO
        self.pdd_state = PDDState.ON_TRACK

    def update_by_position(self, lat: float, lon: float, must_stop: bool, obstacle: bool) -> PDDState:
        if must_stop:
            self.pdd_state = PDDState.STOP
            return self.pdd_state
        if obstacle:
            self.pdd_state = PDDState.RETURNING
            return self.pdd_state
        if not self.route.waypoints:
            self.pdd_state = PDDState.STOP
            return self.pdd_state

        target_lat, target_lon = self.route.waypoints[self.route.current_idx]
        distance = self._distance_m(lat, lon, target_lat, target_lon)
        if distance < 2.0 and self.route.current_idx < len(self.route.waypoints) - 1:
            self.route.current_idx += 1
            self.pdd_state = PDDState.ON_TRACK
        elif distance > self.lane_tolerance_m:
            self.pdd_state = PDDState.OFF_TRACK
        else:
            self.pdd_state = PDDState.ON_TRACK
        return self.pdd_state

    @staticmethod
    def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        # Упрощенная локальная метрика для малых дистанций.
        return sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) * 111_000
