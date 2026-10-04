# MDT Linux Configurator

Linux configuration, control, monitoring, and protocol debugging tool for **MDROBOT MDT-series BLDC motor drivers**.

The initial hardware target is:

- Motor driver: **MD400T**
- Motor: **MDH250**
- Communication: **RS485**
- Host OS: Linux
- Docker targets: **Ubuntu 22.04 / 24.04 / 26.04**

## Project goal

This project is not intended to be a pixel-for-pixel clone of MDAS. The goal is to provide a Linux-native tool that makes the driver easier to understand and debug:

- connect to an MD400T over RS485;
- read and write selected configuration PIDs;
- control Motor 1 / Motor 2 with explicit safety interlocks;
- monitor RPM, current, output, state, position, and digital input data;
- inspect TX/RX traffic;
- visualize every packet as RMID / TMID / ID / PID / length / data / checksum;
- browse protocol definitions in the app.

## Current scope

The first implementation focuses on the PIDs needed for the MD400T + MDH250 workflow. Firmware update, factory reset, preset/tour, and other high-impact advanced functions are intentionally out of scope for v0.1.

### MDH250 profile

The bundled profile records the manual values:

- Rated voltage: 24–48 VDC
- Rated current: 8 A
- Poles: 30
- Encoder resolution: 4096 PPR
- Rated speed: 200 rpm
- Maximum speed: 300 rpm

> **Important:** the MDROBOT communication manual uses both PPR/CPR terminology around encoder-related parameters. The application therefore displays the MDH250 encoder specification, but does **not** automatically write encoder PPR during the v0.1 "Apply profile" operation. Validate encoder scaling against real RPM feedback before enabling that write in production.

## Safety

This software can command physical motors.

Before enabling motor output:

1. lift the driven wheels off the floor or otherwise secure the mechanism;
2. keep people, cables, and tools clear;
3. begin with a low speed such as 20–30 rpm;
4. verify CW/CCW direction;
5. verify Hall/encoder feedback;
6. keep a hardware emergency stop or power disconnect available.

The UI starts disarmed. Motor run commands require an explicit safety acknowledgement.

The software also does **not** automatically disable the driver's limit-switch behavior (PID 17). If the driver requires RUN/BRAKE or START/STOP inputs for your wiring, configure the hardware accordingly and verify the current setting first.

## Quick start

### Native Python

```bash
git clone https://github.com/nayana224/mdt-linux-configurator.git
cd mdt-linux-configurator

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[gui,test]"

mdt-configurator-gui
```

### Docker

Build one of the supported Ubuntu targets:

```bash
./scripts/build.sh 22.04
./scripts/build.sh 24.04
./scripts/build.sh 26.04
```

Run it with an RS485 adapter:

```bash
./scripts/run.sh 24.04 /dev/ttyUSB0
```

The container shares the host Linux kernel. USB serial kernel drivers therefore live on the host; `--device` passes the resulting serial device into the container.

## CLI

List serial ports:

```bash
mdt-configurator ports
```

Read a PID:

```bash
mdt-configurator read --port /dev/ttyUSB0 --id 1 --pid 196
```

Preview a packet without transmitting it:

```bash
mdt-configurator packet --id 1 --pid 21 --data 0f
```

## GUI tabs

- **Connection** — serial port, baud rate, driver ID, connection state
- **Motor Setup** — MDH250 profile, driver/profile comparison, selected writes
- **Control** — Motor 1 / Motor 2 signed RPM commands and free-stop
- **Monitor** — decoded PID 196 / 201 live data
- **Protocol** — PID browser and packet field visualization
- **Log** — decoded TX/RX communication history

## Architecture

```text
PySide6 UI
    |
Application Session
    |
MD400T Device API
    |
MDROBOT Packet Codec
    |
SerialTransport (pyserial)
    |
/dev/ttyUSB*
    |
USB <-> RS485
    |
MD400T
```

The UI never writes directly to the serial port. All traffic passes through the shared session/device/protocol stack so monitoring, logging, and packet visualization use the same packets.

## Protocol basics

The implemented packet format is:

```text
RMID | TMID | ID | PID | DataNumber | DATA... | CHK
 1B     1B    1B   1B       1B        nB       1B
```

For PC/MMI -> motor driver traffic the project uses:

- RMID: 183 (`0xB7`) — motor controller
- TMID: 172 (`0xAC`) — MMI/PC
- default serial: 19200 baud, 8 data bits, 1 stop bit, no parity
- multi-byte data: low byte first
- checksum: two's-complement of the byte sum, so the complete packet sums to zero modulo 256

See [docs/protocol.md](docs/protocol.md) for the implemented PID subset.

## Development

```bash
python -m pip install -e ".[test]"
pytest
```

## Status

This repository is an initial implementation based on the supplied MDROBOT MD400T/MDT-series and MDH250 manuals. **Bench verification against a real MD400T is still required**, especially for adapter direction control, driver firmware differences, encoder scaling, and monitor values.
