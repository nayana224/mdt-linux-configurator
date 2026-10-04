from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitorData:
    rpm: int
    current_a: float
    output: int
    state: int
    position: int
    digital_inputs: int | None

    @property
    def state_flags(self) -> list[str]:
        names = [
            "OVER_VOLT",
            "UNDER_VOLT",
            "OVER_CURRENT",
            "OVER_TEMP",
            "OVER_LOAD",
            "HALL/ENC_FAIL",
            "INV_VEL",
            "STALL",
        ]
        return [name for bit, name in enumerate(names) if self.state & (1 << bit)]


def decode_monitor(data: bytes) -> MonitorData:
    if len(data) not in (11, 12):
        raise ValueError(f"PID_MONITOR requires 11 or 12 data bytes, got {len(data)}")

    rpm = int.from_bytes(data[0:2], "little", signed=True)
    current_raw = int.from_bytes(data[2:4], "little", signed=False)
    output = int.from_bytes(data[4:6], "little", signed=True)
    state = data[6]
    position = int.from_bytes(data[7:11], "little", signed=True)
    di = data[11] if len(data) == 12 else None

    return MonitorData(
        rpm=rpm,
        current_a=current_raw * 0.1,
        output=output,
        state=state,
        position=position,
        digital_inputs=di,
    )
