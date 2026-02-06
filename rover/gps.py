from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class GPSFix:
    lat: float
    lon: float
    speed_mps: float
    hdop: float


class GPSModule:
    """Упрощённый слой GPS (NEO-6M/NEO-M8N)."""

    def __init__(self) -> None:
        self._last_fix = GPSFix(lat=55.751244, lon=37.618423, speed_mps=0.0, hdop=0.8)

    def read_fix(self) -> GPSFix:
        return self._last_fix

    def update_from_nmea(self, points: Iterable[tuple[float, float]]) -> Optional[GPSFix]:
        for lat, lon in points:
            self._last_fix = GPSFix(lat=lat, lon=lon, speed_mps=0.8, hdop=1.2)
            return self._last_fix
        return None
