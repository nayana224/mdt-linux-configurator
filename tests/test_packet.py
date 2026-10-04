import pytest

from mdt_configurator.protocol.packet import Packet, PacketError, checksum, decode_packet


def test_checksum_makes_sum_zero():
    body = bytes([0xB7, 0xAC, 0x01, 0x15, 0x01, 0x0F])
    chk = checksum(body)
    assert (sum(body) + chk) & 0xFF == 0


def test_packet_round_trip():
    packet = Packet(0xB7, 0xAC, 1, 21, b"\x0f")
    raw = packet.encode()
    assert decode_packet(raw) == packet


def test_request_packet():
    raw = Packet.request(1, 196).encode()
    assert raw[:6] == bytes([0xB7, 0xAC, 0x01, 0x04, 0x01, 0xC4])
    assert sum(raw) & 0xFF == 0


def test_decode_rejects_bad_checksum():
    raw = bytearray(Packet(0xB7, 0xAC, 1, 21, b"\x0f").encode())
    raw[-1] ^= 0x01
    with pytest.raises(PacketError, match="checksum"):
        decode_packet(bytes(raw))
