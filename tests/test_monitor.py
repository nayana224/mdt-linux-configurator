from mdt_configurator.protocol.monitor import decode_monitor


def test_decode_monitor_12_bytes():
    data = (
        (30).to_bytes(2, "little", signed=True)
        + (18).to_bytes(2, "little")
        + (250).to_bytes(2, "little", signed=True)
        + bytes([0])
        + (1234).to_bytes(4, "little", signed=True)
        + bytes([0x05])
    )
    monitor = decode_monitor(data)
    assert monitor.rpm == 30
    assert monitor.current_a == 1.8
    assert monitor.output == 250
    assert monitor.state_flags == []
    assert monitor.position == 1234
    assert monitor.digital_inputs == 0x05


def test_decode_state_flags():
    data = b"\x00\x00\x00\x00\x00\x00\xA0\x00\x00\x00\x00"
    monitor = decode_monitor(data)
    assert "HALL/ENC_FAIL" in monitor.state_flags
    assert "STALL" in monitor.state_flags
