from __future__ import annotations

from mdt_configurator.protocol.monitor import MonitorData, decode_monitor
from mdt_configurator.protocol.packet import MID_BLDC, MID_MMI, Packet, i16le, u16le


class MD400T:
    def __init__(self, session: "Session"):
        self.session = session

    @property
    def device_id(self) -> int:
        return self.session.device_id

    def request_pid(self, pid: int) -> Packet:
        return self.session.request_pid(pid)

    def write_u8(self, pid: int, value: int) -> None:
        if not 0 <= value <= 255:
            raise ValueError("uint8 out of range")
        self.session.send(Packet(MID_BLDC, MID_MMI, self.device_id, pid, bytes([value])))

    def write_u16(self, pid: int, value: int) -> None:
        self.session.send(Packet(MID_BLDC, MID_MMI, self.device_id, pid, u16le(value)))

    def command_velocity(self, motor: int, rpm: int) -> None:
        if motor not in (1, 2):
            raise ValueError("motor must be 1 or 2")
        pid = 130 if motor == 1 else 131
        self.session.send(Packet(MID_BLDC, MID_MMI, self.device_id, pid, i16le(rpm)))

    def torque_off(self) -> None:
        self.session.send(Packet(MID_BLDC, MID_MMI, self.device_id, 5, b"\x00"))

    def read_monitor(self, motor: int) -> MonitorData:
        pid = 196 if motor == 1 else 201
        packet = self.request_pid(pid)
        if packet.pid != pid:
            raise ValueError(f"expected PID {pid}, received PID {packet.pid}")
        return decode_monitor(packet.data)

    def read_key_setup(self) -> dict[str, int]:
        result: dict[str, int] = {}
        requests = {
            "limit_switch": 17,
            "hall1": 21,
            "hall2": 65,
            "max_rpm1": 121,
            "max_rpm2": 122,
            "enc_ppr": 156,
        }
        for name, pid in requests.items():
            packet = self.request_pid(pid)
            if len(packet.data) == 1:
                value = packet.data[0]
            elif len(packet.data) == 2:
                value = int.from_bytes(packet.data, "little", signed=False)
            else:
                continue
            result[name] = value
        return result

    def apply_mdh250_safe_subset(self, poles: int = 30, max_rpm: int = 300) -> None:
        if poles % 2:
            raise ValueError("pole count must be even")
        hall_data = poles // 2
        self.write_u8(21, hall_data)
        self.write_u8(65, hall_data)
        self.write_u16(121, max_rpm)
        self.write_u16(122, max_rpm)
