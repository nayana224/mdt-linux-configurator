from __future__ import annotations

import serial
from serial.tools import list_ports

from mdt_configurator.protocol.packet import Packet, decode_packet


def list_serial_ports() -> list[str]:
    return [p.device for p in list_ports.comports()]


class SerialTransport:
    def __init__(self, port: str, baudrate: int = 19200, timeout: float = 0.25):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: serial.Serial | None = None

    @property
    def is_open(self) -> bool:
        return bool(self._serial and self._serial.is_open)

    def open(self) -> None:
        if self.is_open:
            return
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
            write_timeout=self.timeout,
        )
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def close(self) -> None:
        if self._serial:
            self._serial.close()
        self._serial = None

    def write(self, packet: Packet) -> bytes:
        if not self._serial:
            raise RuntimeError("serial port is not open")
        raw = packet.encode()
        self._serial.write(raw)
        self._serial.flush()
        return raw

    def read_packet(self) -> tuple[Packet, bytes]:
        if not self._serial:
            raise RuntimeError("serial port is not open")

        header = self._serial.read(5)
        if len(header) != 5:
            raise TimeoutError(f"timed out waiting for packet header ({len(header)}/5 bytes)")

        data_len = header[4]
        tail = self._serial.read(data_len + 1)
        if len(tail) != data_len + 1:
            raise TimeoutError(
                f"timed out waiting for packet payload ({len(tail)}/{data_len + 1} bytes)"
            )

        raw = header + tail
        return decode_packet(raw), raw

    def transact(self, packet: Packet, expect_response: bool) -> tuple[bytes, Packet | None, bytes | None]:
        tx = self.write(packet)
        if not expect_response:
            return tx, None, None
        rx, raw = self.read_packet()
        return tx, rx, raw
