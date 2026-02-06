from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List


@dataclass
class RoverStore:
    rovers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    command_queues: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    lock: Lock = field(default_factory=Lock)

    def upsert_status(self, rover_id: str, status: Dict[str, Any]) -> None:
        with self.lock:
            self.rovers[rover_id] = status

    def list_rovers(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                {
                    "id": rover_id,
                    "mode": payload.get("mode", "MANUAL"),
                    "pdd_state": payload.get("pdd_state", "STOP"),
                    "gps": payload.get("gps", {}),
                }
                for rover_id, payload in self.rovers.items()
            ]

    def get_rover(self, rover_id: str) -> Dict[str, Any]:
        with self.lock:
            return self.rovers.get(rover_id, {})

    def enqueue_command(self, rover_id: str, command: Dict[str, Any]) -> None:
        with self.lock:
            self.command_queues[rover_id].append(command)

    def pop_commands(self, rover_id: str) -> List[Dict[str, Any]]:
        with self.lock:
            items = self.command_queues[rover_id][:]
            self.command_queues[rover_id].clear()
            return items
