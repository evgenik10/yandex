from dataclasses import dataclass
from enum import Enum
from typing import Dict


class DriveCommand(str, Enum):
    STOP = "STOP"
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass
class MotorState:
    left_pwm: int = 0
    right_pwm: int = 0
    command: DriveCommand = DriveCommand.STOP


class MotorController:
    """Абстракция моторов и драйвера TB6612/L298N."""

    def __init__(self, max_pwm: int = 100):
        self.max_pwm = max_pwm
        self.state = MotorState()

    def apply(self, command: DriveCommand, speed: int) -> MotorState:
        speed = max(0, min(speed, self.max_pwm))
        if command == DriveCommand.FORWARD:
            self.state = MotorState(speed, speed, command)
        elif command == DriveCommand.BACKWARD:
            self.state = MotorState(-speed, -speed, command)
        elif command == DriveCommand.LEFT:
            self.state = MotorState(-speed, speed, command)
        elif command == DriveCommand.RIGHT:
            self.state = MotorState(speed, -speed, command)
        else:
            self.state = MotorState(0, 0, DriveCommand.STOP)
        return self.state

    def emergency_stop(self) -> MotorState:
        return self.apply(DriveCommand.STOP, 0)

    def as_dict(self) -> Dict[str, int | str]:
        return {
            "left_pwm": self.state.left_pwm,
            "right_pwm": self.state.right_pwm,
            "command": self.state.command.value,
        }
