from __future__ import annotations

from dataclasses import dataclass

MID_MMI = 172
MID_BLDC = 183


class PacketError(ValueError):
    """Raised when an MDROBOT packet is malformed."""


def checksum(data: bytes) -> int:
    """Return the two's-complement checksum byte."""
    return (-sum(data)) & 0xFF


@dataclass(frozen=True)
class Packet:
    rmid: int
    tmid: int
    device_id: int
    pid: int
    data: bytes = b""

    def __post_init__(self) -> None:
        for name, value in (
            ("rmid", self.rmid),
            ("tmid", self.tmid),
            ("device_id", self.device_id),
            ("pid", self.pid),
        ):
            if not 0 <= value <= 0xFF:
                raise PacketError(f"{name} out of byte range: {value}")
        if len(self.data) > 0xFF:
            raise PacketError("data payload is too large")

    def encode(self) -> bytes:
        body = bytes(
            [self.rmid, self.tmid, self.device_id, self.pid, len(self.data)]
        ) + self.data
        return body + bytes([checksum(body)])

    def hex(self) -> str:
        return " ".join(f"{b:02X}" for b in self.encode())

    @classmethod
    def request(cls, device_id: int, requested_pid: int) -> "Packet":
        return cls(
            rmid=MID_BLDC,
            tmid=MID_MMI,
            device_id=device_id,
            pid=4,
            data=bytes([requested_pid & 0xFF]),
        )


def decode_packet(raw: bytes) -> Packet:
    if len(raw) < 6:
        raise PacketError(f"packet too short: {len(raw)} bytes")

    data_len = raw[4]
    expected = 6 + data_len
    if len(raw) != expected:
        raise PacketError(f"length mismatch: expected {expected}, got {len(raw)}")

    if sum(raw) & 0xFF:
        raise PacketError("checksum mismatch")

    return Packet(
        rmid=raw[0],
        tmid=raw[1],
        device_id=raw[2],
        pid=raw[3],
        data=bytes(raw[5:-1]),
    )


def i16le(value: int) -> bytes:
    if not -32768 <= value <= 32767:
        raise ValueError("int16 out of range")
    return int(value).to_bytes(2, "little", signed=True)


def u16le(value: int) -> bytes:
    if not 0 <= value <= 65535:
        raise ValueError("uint16 out of range")
    return int(value).to_bytes(2, "little", signed=False)
