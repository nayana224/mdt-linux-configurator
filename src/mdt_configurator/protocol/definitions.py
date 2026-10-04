from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PidDefinition:
    pid: int
    name: str
    access: str
    size: str
    description: str
    category: str
    notes: str = ""


def _p(pid: int, name: str, access: str, size: str, description: str, category: str, notes: str = "") -> PidDefinition:
    return PidDefinition(pid, name, access, size, description, category, notes)


PID_DEFINITIONS = {
    1: _p(1, "PID_VER", "R", "1", "Driver program version.", "Device"),
    4: _p(4, "PID_REQ_PID_DATA", "C", "1", "Request the value of another PID.", "Protocol"),
    5: _p(5, "PID_TQ_OFF", "C", "1", "Free stop / torque off.", "Control"),
    10: _p(10, "PID_COMMAND", "C", "1", "General command selector.", "Control"),
    17: _p(17, "PID_USE_LIMIT_SW", "R/W", "1", "Use CTRL RUN/BRAKE and START/STOP inputs as communication-drive limit switches.", "Safety", "The application never changes this automatically."),
    21: _p(21, "PID_HALL_TYPE", "R/W", "1", "Motor 1 Hall sensor pole setting.", "Motor setup", "For pole counts not in the special mapping table, DATA = poles / 2."),
    25: _p(25, "PID_INPUT_TYPE", "R/W", "1", "Control input type.", "Motor setup"),
    65: _p(65, "PID_HALL2_TYPE", "R/W", "1", "Motor 2 Hall sensor pole setting.", "Motor setup"),
    121: _p(121, "PID_MAX_RPM1", "R/W", "2", "Motor 1 maximum speed in rpm.", "Motor setup"),
    122: _p(122, "PID_MAX_RPM2", "R/W", "2", "Motor 2 maximum speed in rpm.", "Motor setup"),
    130: _p(130, "PID_VEL_CMD", "C", "2", "Motor 1 speed command in rpm; negative=CW, positive=CCW per manual.", "Control"),
    131: _p(131, "PID_VEL_CMD2", "C", "2", "Motor 2 speed command in rpm.", "Control"),
    149: _p(149, "PID_RETURN_TYPE", "R/W", "2", "Select return-data type for commands.", "Protocol"),
    156: _p(156, "PID_ENC_PPR", "R/W", "2", "Encoder pulses-per-revolution setting for encoder speed control.", "Motor setup", "Manual wording also refers to CPR; MDH250 4096 PPR must be bench-verified before automatic writes."),
    193: _p(193, "PID_MAIN_DATA", "R", "17", "Motor 1 main data.", "Monitor"),
    196: _p(196, "PID_MONITOR", "R", "11/12", "Motor 1 monitor data.", "Monitor"),
    200: _p(200, "PID_MAIN_DATA2", "R", "17", "Motor 2 main data.", "Monitor"),
    201: _p(201, "PID_MONITOR2", "R", "11/12", "Motor 2 monitor data.", "Monitor"),
}


def get_pid(pid: int) -> PidDefinition | None:
    return PID_DEFINITIONS.get(pid)
