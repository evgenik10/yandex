import os
import time
from typing import Dict, List

from api_client import ControlServerClient, RoverStatus
from camera import CameraHub
from gps import GPSModule
from motors import DriveCommand, MotorController
from navigation import Navigator, RoverMode
from sensors import UltrasonicSensor
from vision import VisionEngine


def handle_command(cmd: Dict, navigator: Navigator, motors: MotorController) -> None:
    kind = cmd.get("type")
    payload = cmd.get("payload", {})

    if kind == "set_mode":
        navigator.mode = RoverMode(payload.get("mode", "MANUAL"))
    elif kind == "route":
        navigator.set_route(payload.get("waypoints", []))
    elif kind == "drive":
        motors.apply(DriveCommand(payload.get("command", "STOP")), payload.get("speed", 30))
    elif kind == "stop":
        motors.emergency_stop()


def main() -> None:
    rover_id = os.getenv("ROVER_ID", "rover-01")
    server_url = os.getenv("CONTROL_SERVER_URL", "http://127.0.0.1:8000")

    gps = GPSModule()
    motors = MotorController()
    sensor = UltrasonicSensor()
    vision = VisionEngine()
    camera_hub = CameraHub()
    navigator = Navigator()
    client = ControlServerClient(server_url, rover_id)

    while True:
        fix = gps.read_fix()
        obstacle = sensor.read_distance()
        detections_by_camera: Dict[str, List] = {
            camera_id: vision.infer(camera_id) for camera_id in camera_hub.cameras.keys()
        }
        summary = vision.summarize(detections_by_camera)
        pdd = navigator.update_by_position(fix.lat, fix.lon, summary["must_stop"], obstacle.is_blocked)

        if pdd == "STOP":
            motors.emergency_stop()

        status = RoverStatus(
            rover_id=rover_id,
            mode=navigator.mode.value,
            pdd_state=pdd.value if hasattr(pdd, "value") else pdd,
            gps=fix.__dict__,
            motors=motors.as_dict(),
            streams=camera_hub.list_streams(),
            detections=summary["detections"],
        )
        try:
            client.push_status(status)
            commands = client.poll_commands()
            for cmd in commands:
                handle_command(cmd, navigator, motors)
        except Exception:
            pass

        time.sleep(0.2)


if __name__ == "__main__":
    main()
