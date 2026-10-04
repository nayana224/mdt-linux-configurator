from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from mdt_configurator.protocol.packet import MID_BLDC, MID_MMI, Packet
from mdt_configurator.transport.serial_transport import SerialTransport


@dataclass(frozen=True)
class TrafficEvent:
    timestamp: datetime
    direction: str
    raw: bytes
    packet: Packet | None
    note: str = ""

    @property
    def hex(self) -> str:
        return " ".join(f"{b:02X}" for b in self.raw)


class Session:
    def __init__(self) -> None:
        self.device_id = 1
        self.transport: SerialTransport | None = None
        self.listeners: list[Callable[[TrafficEvent], None]] = []

    @property
    def connected(self) -> bool:
        return bool(self.transport and self.transport.is_open)

    def add_listener(self, callback: Callable[[TrafficEvent], None]) -> None:
        self.listeners.append(callback)

    def _emit(self, event: TrafficEvent) -> None:
        for callback in list(self.listeners):
            callback(event)

    def connect(self, port: str, baudrate: int = 19200, device_id: int = 1) -> None:
        self.disconnect()
        self.device_id = device_id
        self.transport = SerialTransport(port=port, baudrate=baudrate)
        self.transport.open()

    def disconnect(self) -> None:
        if self.transport:
            self.transport.close()
        self.transport = None

    def send(self, packet: Packet) -> None:
        if not self.transport:
            raise RuntimeError("not connected")
        tx, _, _ = self.transport.transact(packet, expect_response=False)
        self._emit(TrafficEvent(datetime.now(), "TX", tx, packet))

    def request_pid(self, pid: int) -> Packet:
        if not self.transport:
            raise RuntimeError("not connected")
        request = Packet.request(self.device_id, pid)
        tx, response, rx_raw = self.transport.transact(request, expect_response=True)
        self._emit(TrafficEvent(datetime.now(), "TX", tx, request, note=f"request PID {pid}"))
        assert response is not None and rx_raw is not None
        self._emit(TrafficEvent(datetime.now(), "RX", rx_raw, response))
        return response

    def make_packet(self, pid: int, data: bytes) -> Packet:
        return Packet(MID_BLDC, MID_MMI, self.device_id, pid, data)
