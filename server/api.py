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

    def create_rover(self, rover_id: str) -> Dict[str, Any]:
        with self.lock:
            if rover_id not in self.rovers:
                self.rovers[rover_id] = {
                    "id": rover_id,
                    "mode": "MANUAL",
                    "pdd_state": "STOP",
                    "gps": {},
                    "streams": {
                        "front": "Front stream",
                        "rear": "Rear stream",
                        "left": "Left stream",
                        "right": "Right stream",
                    },
                    "route": [],
                    "goal": None,
                }
            return self.rovers[rover_id]

    def upsert_status(self, rover_id: str, status: Dict[str, Any]) -> None:
        with self.lock:
            current = self.rovers.get(rover_id, {"id": rover_id})
            merged = {**current, **status, "id": rover_id}
            self.rovers[rover_id] = merged

    def list_rovers(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                {
                    "id": rover_id,
                    "mode": payload.get("mode", "MANUAL"),
                    "pdd_state": payload.get("pdd_state", "STOP"),
                    "gps": payload.get("gps", {}),
                }
                for rover_id, payload in sorted(self.rovers.items())
            ]

    def get_rover(self, rover_id: str) -> Dict[str, Any]:
        with self.lock:
            return self.rovers.get(rover_id, {})

    def set_goal(self, rover_id: str, goal: Dict[str, Any]) -> Dict[str, Any]:
        with self.lock:
            if rover_id not in self.rovers:
                self.rovers[rover_id] = {"id": rover_id, "mode": "MANUAL", "pdd_state": "STOP", "gps": {}, "streams": {}, "route": []}
            self.rovers[rover_id]["goal"] = goal
            return self.rovers[rover_id]

    def enqueue_command(self, rover_id: str, command: Dict[str, Any]) -> None:
        with self.lock:
            self.command_queues[rover_id].append(command)

    def pop_commands(self, rover_id: str) -> List[Dict[str, Any]]:
        with self.lock:
            items = self.command_queues[rover_id][:]
            self.command_queues[rover_id].clear()
            return items
