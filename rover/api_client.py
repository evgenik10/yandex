from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import requests


@dataclass
class RoverStatus:
    rover_id: str
    mode: str
    pdd_state: str
    gps: Dict[str, Any]
    motors: Dict[str, Any]
    streams: Dict[str, str]
    detections: List[Dict[str, Any]]


class ControlServerClient:
    def __init__(self, base_url: str, rover_id: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.rover_id = rover_id
        self.api_key = api_key

    @property
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def push_status(self, status: RoverStatus) -> None:
        requests.post(
            f"{self.base_url}/rovers/{self.rover_id}/status",
            json=asdict(status),
            headers=self._headers,
            timeout=2,
        )

    def poll_commands(self) -> List[Dict[str, Any]]:
        response = requests.get(
            f"{self.base_url}/rovers/{self.rover_id}/commands",
            headers=self._headers,
            timeout=2,
        )
        response.raise_for_status()
        return response.json().get("items", [])
