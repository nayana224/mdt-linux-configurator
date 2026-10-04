# Architecture

## Goal

Keep GUI state, motor-driver semantics, packet encoding, and serial I/O separate so that each layer can be tested independently.

```text
PySide6 tabs
    |
    v
Session / application state
    |
    v
MD400T device API
    |
    v
Packet codec + PID definitions
    |
    v
pyserial transport
    |
    v
/dev/ttyUSB*
```

## Invariants

- UI code does not call `serial.write()` directly.
- Every TX/RX packet goes through the shared session so it can be logged.
- Multi-byte protocol data is little-endian (low byte first).
- Motor output starts disarmed.
- The bundled MDH250 profile caps UI commands at 300 rpm.
- PID 17 is never changed automatically.
- Encoder PPR is not automatically written until real hardware scaling is verified.

## Tabs

### Connection
Owns port selection and connection lifecycle.

### Motor Setup
Reads key PIDs and writes the conservative MDH250 subset:
- PID 21 Hall type Motor 1 = 15
- PID 65 Hall type Motor 2 = 15
- PID 121 Max RPM Motor 1 = 300
- PID 122 Max RPM Motor 2 = 300

### Control
Sends PID 130 / 131 signed-rpm commands and PID 5 free-stop.

### Monitor
Requests PID 196 and 201 and decodes RPM/current/output/state/position/DI.

### Protocol
Uses the same packet codec as real communication. The visualized bytes are therefore the bytes that the transport would transmit.

### Log
Receives traffic events from Session and shows decoded PID names plus raw bytes.
